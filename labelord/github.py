import click
import requests
from .helpers import *


@click.pass_context
def get_response(ctx, uri):
    '''
    Gets a response from GitHub API.

    :param uri: Part of URL after https://api.github.com/ to retrieve response from.
    :return: Tuple of response and status code.
    '''
    session = ctx.obj.get('session', requests.Session())
    response = session.get('https://api.github.com/' + uri)
    if response.status_code == 401:
        error(4, 'GitHub: ERROR {} - {}'.format(response.status_code, response.json().get('message', '')))
    return response, response.status_code


def update_label(session, repo, label, data):
    '''
    Updates a label with given data.

    :param session: Session to use for communication with GitHub API.
    :param repo: Full repository name where is label to be changed.
    :param label: Name of the label to be changed.
    :param data: Data in JSON format for the label to be updated to, containing name and color keys.
    :return: Tuple of status code and response message if some error occured, otherwise None.
    '''
    response = session.patch('https://api.github.com/repos/{}/labels/{}'.format(repo, label), json=data)
    if response.status_code == 200:
        return response.status_code, None
    return response.status_code, response.json().get('message', '')


def add_label(session, repo, data):
    '''
    Adds a label with given data.

    :param session: Session to use for communication with GitHub API.
    :param repo: Full repository name where is label to be changed.
    :param data: Data in JSON format for the label to be added, containing name and color keys.
    :return: Tuple of status code and response message if some error occured, otherwise None.
    '''
    response = session.post('https://api.github.com/repos/{}/labels'.format(repo), json=data)
    if response.status_code == 201:
        return response.status_code, None
    return response.status_code, response.json().get('message', '')


def delete_label(session, repo, label):
    '''
    Deletes a label with given name from the repository.

    :param session: Session to use for communication with GitHub API.
    :param repo: Full repository name where is label to be changed.
    :param label: Name of the label to be removed.
    :return: Tuple of status code and response message if some error occured, otherwise None.
    '''
    response = session.delete('https://api.github.com/repos/{}/labels/{}'.format(repo, label))
    if response.status_code == 204:
        return response.status_code, None
    return response.status_code, response.json().get('message', '')


def log_suc(action_tag, dry_tag, repo, label, color):
    '''
    Logs successfull action.

    :param action_tag: Tag for action done.
    :param dry_tag: Tag indicating dry run or not.
    :param repo: Repository name.
    :param label: Label name.
    :param color: Label color.
    '''
    print('[{}][{}] {}; {}; {}'.format(action_tag, dry_tag, repo, label, color))


def log_err(tag, repo, label, color, code, msg):
    '''
    Logs unsuccessful action.

    :param tag: Tag for action done unsuccessfully.
    :param repo: Repository name.
    :param label: Label name.
    :param color: Label color.
    :param code: Response code.
    :param msg: Response message.
    '''
    print('[{}][ERR] {}; {}; {}; {} - {}'.format(tag, repo, label, color, code, msg))


def perform_operation(replace, repos, labels, dry_run, logging, session):
    '''
    Performs a given operation with labels on GitHub repositories.

    :param replace: True if labels should be completely replaced by the templates.
    :param repos: Full names of the repositories for the action to be performed on.
    :param labels: Names of the template labels.
    :param dry_run: True if operation should not be done on actual GitHub repositories.
    :param logging: 1 if logs should be printed on stdout, 0 otherwise.
    :param session: Session to use for communication with GitHub API.
    '''
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
                                log_suc('UPD', 'SUC', repo, label, labels[label])
                                # print('[UPD][SUC] {}; {}; {}'.format(repo, label, labels[label]))
                            elif response_code != 200 and logging == 1:
                                log_err('UPD', repo, label, labels[label], response_code, message)
                                # print('[UPD][ERR] {}; {}; {}; {} - {}'.format(repo, label, labels[label], response_code, message))
                                errors += 1
                            elif response_code != 200 and logging == 0:
                                error(0, 'ERROR: UPD; {}; {}; {}; {} - {}'.format(repo, label, labels[label], response_code, message))
                                errors += 1
                            elif response_code != 200:
                                errors += 1
                        else:
                            if logging == 1:
                                log_suc('UPD', 'DRY', repo, label, labels[label])
                                # print('[UPD][DRY] {}; {}; {}'.format(repo, label, labels[label]))
                else:
                    if not dry_run:
                        add_data = {"name": label, "color": labels[label]}
                        response_code, message = add_label(session, repo, add_data)
                        if response_code == 201 and logging == 1:
                            log_suc('ADD', 'SUC', repo, label, labels[label])
                            # print('[ADD][SUC] {}; {}; {}'.format(repo, label, labels[label]))
                        elif response_code != 201 and logging == 1:
                            log_err('ADD', repo, label, labels[label], response_code, message)
                            # print('[ADD][ERR] {}; {}; {}; {} - {}'.format(repo, label, labels[label], response_code, message))
                            errors += 1
                        elif response_code != 201 and logging == 0:
                            error(0, 'ERROR: ADD; {}; {}; {}; {} - {}'.format(repo, label, labels[label], response_code, message))
                            errors += 1
                        elif response_code != 201:
                            errors += 1
                    else:
                        if logging == 1:
                            log_suc('ADD', 'DRY', repo, label, labels[label])
                            # print('[ADD][DRY] {}; {}; {}'.format(repo, label, labels[label]))
            for label in labels_to_delete:
                if not dry_run:
                    response_code, message = delete_label(session, repo, label)
                    if response_code == 204 and logging == 1:
                        log_suc('DEL', 'SUC', repo, label, repo_labels[label])
                        # print('[DEL][SUC] {}; {}; {}'.format(repo, label, repo_labels[label]))
                    elif response_code != 204 and logging == 1:
                        log_err('DEL', repo, label, repo_labels[label], response_code, message)
                        # print('[DEL][ERR] {}; {}; {}; {} - {}'.format(repo, label, repo_labels[label], response_code, message))
                        errors += 1
                    elif response_code != 204 and logging == 0:
                        error(0, 'ERROR: DEL; {}; {}; {}; {} - {}'.format(repo, label, repo_labels[label], response_code, message))
                        errors += 1
                    elif response_code != 204:
                        errors += 1
                else:
                    if logging == 1:
                        log_suc('DEL', 'SUC', repo, label, repo_labels[label])
                        # print('[DEL][DRY] {}; {}; {}'.format(repo, label, repo_labels[label]))
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
    '''
    Gets labels names and color from repository.

    :param template_repository: Full name of the template repository.
    :param config: Config loaded with configparser to be used as a template if template_repository is not provided.
    :return: Dictionary of label names as keys and labels colors as values.
    '''
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
    '''
    Gets full repositories names which should be used to work with Labelord application.

    :param all_repos: True if all users repositories should be used.
    :param config: Config loaded with configparser which contains repositories to be used.
    :return: Array of full repositories names.
    '''
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
