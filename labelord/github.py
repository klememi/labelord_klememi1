import click
import requests
from .helpers import *


@click.pass_context
def get_response(ctx, uri):
    session = ctx.obj.get('session', requests.Session())
    response = session.get('https://api.github.com/' + uri)
    if response.status_code == 401:
        error(4, 'GitHub: ERROR {} - {}'.format(response.status_code, response.json().get('message', '')))
    return response, response.status_code


def update_label(session, repo, label, data):
    response = session.patch('https://api.github.com/repos/{}/labels/{}'.format(repo, label), json=data)
    if response.status_code == 200:
        return response.status_code, None
    return response.status_code, response.json().get('message', '')


def add_label(session, repo, data):
    response = session.post('https://api.github.com/repos/{}/labels'.format(repo), json=data)
    if response.status_code == 201:
        return response.status_code, None
    return response.status_code, response.json().get('message', '')


def delete_label(session, repo, label):
    response = session.delete('https://api.github.com/repos/{}/labels/{}'.format(repo, label))
    if response.status_code == 204:
        return response.status_code, None
    return response.status_code, response.json().get('message', '')


def perform_operation(replace, repos, labels, dry_run, logging, session):
    errors = 0
    update_repos = set()
    for repo in repos:
        response, code = get_response('repos/{}/labels?per_page=100&page=1'.format(repo))
        if code == 200:
            update_repos.add(repo)
            repo_labels = {label['name']: label['color'] for label in response.json()}
            labels_to_delete = set()
            if replace:
                labels_to_delete = {label for label in repo_labels} - {label for label in labels}
            for label in labels:
                if label.lower() in (repo_label.lower() for repo_label in repo_labels):
                    rlabel = list(filter(lambda rlabel: rlabel == label.lower(), (rlabel.lower() for rlabel in repo_labels)))[0]
                    if labels.get(label, 'label') != repo_labels.get(label, 'repo_label'):
                        if not dry_run:
                            update_data = {"name": label, "color": labels[label]}
                            response_code, message = update_label(session, repo, rlabel, update_data)
                            if response_code == 200 and logging == 1:
                                print('[UPD][SUC] {}; {}; {}'.format(repo, label, labels[label]))
                            elif response_code != 200 and logging == 1:
                                print('[UPD][ERR] {}; {}; {}; {} - {}'.format(repo, label, labels[label], response_code, message))
                                errors += 1
                            elif response_code != 200 and logging == 0:
                                error(0, 'ERROR: UPD; {}; {}; {}; {} - {}'.format(repo, label, labels[label], response_code, message))
                                errors += 1
                            elif response_code != 200:
                                errors += 1
                        else:
                            if logging == 1:
                                print('[UPD][DRY] {}; {}; {}'.format(repo, label, labels[label]))
                else:
                    if not dry_run:
                        add_data = {"name": label, "color": labels[label]}
                        response_code, message = add_label(session, repo, add_data)
                        if response_code == 201 and logging == 1:
                            print('[ADD][SUC] {}; {}; {}'.format(repo, label, labels[label]))
                        elif response_code != 201 and logging == 1:
                            print('[ADD][ERR] {}; {}; {}; {} - {}'.format(repo, label, labels[label], response_code, message))
                            errors += 1
                        elif response_code != 201 and logging == 0:
                            error(0, 'ERROR: ADD; {}; {}; {}; {} - {}'.format(repo, label, labels[label], response_code, message))
                            errors += 1
                        elif response_code != 201:
                            errors += 1
                    else:
                        if logging == 1:
                            print('[ADD][DRY] {}; {}; {}'.format(repo, label, labels[label]))
            for label in labels_to_delete:
                if not dry_run:
                    response_code, message = delete_label(session, repo, label)
                    if response_code == 204 and logging == 1:
                        print('[DEL][SUC] {}; {}; {}'.format(repo, label, repo_labels[label]))
                    elif response_code != 204 and logging == 1:
                        print('[DEL][ERR] {}; {}; {}; {} - {}'.format(repo, label, repo_labels[label], response_code, message))
                        errors += 1
                    elif response_code != 204 and logging == 0:
                        error(0, 'ERROR: DEL; {}; {}; {}; {} - {}'.format(repo, label, repo_labels[label], response_code, message))
                        errors += 1
                    elif response_code != 204:
                        errors += 1
                else:
                    if logging == 1:
                        print('[DEL][DRY] {}; {}; {}'.format(repo, label, repo_labels[label]))
        elif logging == 1:
            print('[LBL][ERR] {}; {} - {}'.format(repo, code, response.json().get('message', '')))
            errors += 1
        elif logging == 0:
            error(0, 'ERROR: LBL; {}; {} - {}'.format(repo, code, response.json().get('message', '')))
            errors += 1
        else:
            errors += 1
    if errors > 0:
        if logging == 1:
            print('[SUMMARY] {} error(s) in total, please check log above'.format(errors))
        elif logging == 0:
            print('SUMMARY: {} error(s) in total, please check log above'.format(errors))
        error(10)
    elif logging == 1:
        print('[SUMMARY] {} repo(s) updated successfully'.format(len(update_repos)))
    elif logging == 0:
        print('SUMMARY: {} repo(s) updated successfully'.format(len(update_repos)))


def get_labels(template_repository, config):
    if template_repository:
        response, code = get_response('repos/{}/labels?per_page=100&page=1'.format(template_repository))
        if code == 200:
            return {label['name']: label['color'] for label in response.json()}
        else:
            error(10, response.json().get('message', ''))
    elif 'labels' in config:
        return {label: config['labels'][label] for label in config['labels']}
    else:
        error(6, 'No labels specification has been found')


def get_repos(all_repos, config):
    if all_repos:
        response, code = get_response('user/repos?per_page=100&page=1')
        if code == 200:
            return [repo['full_name'] for repo in response.json()]
        else:
            error(10, response.json().get('message', ''))
    elif 'repos' in config:
        return [repo for repo in config['repos'] if config['repos'].getboolean(repo)]
    else:
        error(7, 'No repositories specification has been found')


def sync_labels(event, repos, label, color, old_label):
    session = app.ghsession
    if not session:
        session = requests.Session()
        session.headers = {'User-Agent': 'mi-pyt-02-labelord'}
        github_token = app.lblconfig['github']['token']
        if not github_token:
            error(3, 'No GitHub token has been provided')
        def token_auth(req):
            req.headers['Authorization'] = 'token ' + github_token
            return req
        session.auth = token_auth
    if event == 'created':
        for repo in repos:
            data = {"name": label, "color": color}
            code, msg = add_label(session, repo, data)
    elif event == 'edited':
        for repo in repos:
            data = {"name": label, "color": color}
            code, msg = update_label(session, repo, old_label, data)
    else:
        # deleted
        for repo in repos:
            code, msg = delete_label(session, repo, label)
    return flask.make_response('OK', 200)
