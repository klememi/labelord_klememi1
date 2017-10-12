# MI-PYT, task 1 (requests+click)
# File: labelord.py
# TODO: create requirements.txt and install
import click
import requests
import configparser
import sys


@click.group('labelord')
@click.option('-c', '--config', default='./config.cfg', help='Configuration file path.')
@click.option('-t', '--token', envvar='GITHUB_TOKEN', default='', help='GitHub token.')
@click.option('-y', '--colorful', is_flag=True, help='Turns on colors for logs.')
@click.version_option(version=0.1, prog_name='labelord')
@click.pass_context
def cli(ctx, config, token, colorful):
    cfg = configparser.ConfigParser()
    cfg.optionxform = str
    cfg.read(config)
    cfgtoken = cfg.get('github', 'token', fallback='')
    ctx.obj['token'] = token if token else cfgtoken
    ctx.obj['colorful'] = colorful
    ctx.obj['config'] = cfg


@cli.command()
@click.pass_context
def list_repos(ctx):
    """List accessible repositories."""
    set_session()
    page = 1
    response, code = get_response('user/repos?per_page=100&page={}'.format(page))
    if code == 200:
        while response.json():
            for repo in response.json():
                print(repo['full_name'])
            page += 1
            response, code = get_response('user/repos?per_page=100&page={}'.format(page))
    else:
        error(10)


@cli.command()
@click.argument('reposlug', metavar='REPOSITORY')
@click.pass_context
def list_labels(ctx, reposlug):
    """List labels of desired repository."""
    set_session()
    page = 1
    response, code = get_response('repos/{}/labels?per_page=100&page={}'.format(reposlug, page))
    if code == 200:
        while response.json():
            for label in response.json():
                print('#{} {}'.format(label['color'], label['name']))
            page += 1
            response, code = get_response('repos/{}/labels?per_page=100&page={}'.format(reposlug, page))
    elif code == 404:
        error(5, 'GitHub: ERROR {} - {}'.format('404', response.json()['message']))
    else:
        error(10)


@cli.command()
@click.argument('mode', type=click.Choice(['update', 'replace']), metavar='<update|replace>')
@click.option('-a', '--all-repos', is_flag=True, help='Use all accessible repositories.')
@click.option('-d', '--dry-run', is_flag=True, help='Doesn\'t make any changes to GitHub, just prints them.')
@click.option('-v', '--verbose', is_flag=True, help='Turns on logs on standard output.')
@click.option('-q', '--quiet', is_flag=True, help='Turns off all logs.')
@click.option('-r', '--template-repo', default='', help='Repository to use as a template.')
@click.pass_context
def run(ctx, mode, all_repos, dry_run, verbose, quiet, template_repo):
    """Run labels processing."""
    set_session()
    config = ctx.obj.get('config')
    template_repository = template_repo if template_repo else config.get('others', 'template-repo', fallback='')
    labels = get_labels(template_repository, config)
    repos = get_repos(all_repos, config)
    logging = 0
    logging += 1 if verbose else 0
    logging += 2 if quiet else 0
    perform_operation(True if mode == 'replace' else False, repos, labels, dry_run, logging)


@click.pass_context
def set_session(ctx):
    session = ctx.obj.get('session', requests.Session())
    session.headers = {'User-Agent': 'mi-pyt-01-labelord'}
    github_token = ctx.obj.get('token')
    if not github_token:
        error(3, 'No GitHub token has been provided')
    def token_auth(req):
        req.headers['Authorization'] = 'token ' + github_token
        return req
    session.auth = token_auth
    ctx.obj['session'] = session


def error(return_value, *args, **kwargs):
    if args:
        print(*args, file=sys.stderr, **kwargs)
    if return_value > 0:
        sys.exit(return_value)


@click.pass_context
def get_response(ctx, uri):
    session = ctx.obj.get('session', requests.Session())
    response = session.get('https://api.github.com/' + uri)
    if response.status_code == 401:
        error(4, 'GitHub: ERROR {} - {}'.format(response.status_code, response.json()['message']))
    return response, response.status_code


@click.pass_context
def update_label(ctx, repo, label, data):
    session = ctx.obj.get('session', requests.Session())
    response = session.patch('https://api.github.com/repos/{}/labels/{}'.format(repo, label), data)
    return response.status_code, response.json()['message']


@click.pass_context
def add_label(ctx, repo, data):
    session = ctx.obj.get('session', requests.Session())
    response = session.post('https://api.github.com/repos/{}/labels'.format(repo), data)
    return response.status_code, response.json()['message']


@click.pass_context
def delete_label(ctx, repo, label):
    session = ctx.obj.get('session', requests.Session())
    response = session.delete('https://api.github.com/repos/{}/labels/{}'.format(repo, label))
    return response.status_code, response.json()['message']


def perform_operation(replace, repos, labels, dry_run, logging):
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
                if label in repo_labels.keys():
                    if labels[label] != repo_labels[label]:
                        if not dry_run:
                            update_data = {"name": label, "color": labels[label]}
                            response_code, message = update_label(repo, label, update_data)
                            if response_code == 200:
                                print('[UPD][SUC] {}; {}; {}'.format(repo, label, labels[label]))
                                update_repos.add(repo)
                            elif logging == 1:
                                print('[UPD][ERR] {}; {}; {}; {} - {}'.format(repo, label, labels[label], response_code, message))
                                errors += 1
                            elif logging == 0 or logging == 3:
                                error(0, 'ERROR: UPD; {}; {}; {}; {} - {}'.format(repo, label, labels[label], response_code, message))
                                errors += 1
                        else:
                            update_repos.add(repo)
                            if logging == 1:
                                print('[UPD][DRY] {}; {}; {}'.format(repo, label, labels[label]))
                else:
                    if not dry_run:
                        add_data = {"name": label, "color": labels[label]}
                        response_code, message = add_label(repo, add_data)
                        if response_code == 201:
                            print('[ADD][SUC] {}; {}; {}'.format(repo, label, labels[label]))
                            update_repos.add(repo)
                        elif logging == 1:
                            print('[ADD][ERR] {}; {}; {}; {} - {}'.format(repo, label, labels[label], response_code, message))
                            errors += 1
                        elif logging == 0 or logging == 3:
                            error(0, 'ERROR: ADD; {}; {}; {}; {} - {}'.format(repo, label, labels[label], response_code, message))
                            errors += 1
                    else:
                        update_repos.add(repo)
                        if logging == 1:
                            print('[ADD][DRY] {}; {}; {}'.format(repo, label, labels[label]))
            for label in labels_to_delete:
                if not dry_run:
                    response_code, message = delete_label(repo, label)
                    if response_code == 204:
                        print('[DEL][SUC] {}; {}; {}'.format(repo, label, labels[label]))
                        update_repos.add(repo)
                    elif logging == 1:
                        print('[DEL][ERR] {}; {}; {}; {} - {}'.format(repo, label, labels[label], response_code, message))
                        errors += 1
                    elif logging == 0 or logging == 3:
                        error(0, 'ERROR: DEL; {}; {}; {}; {} - {}'.format(repo, label, labels[label], response_code, message))
                        errors += 1
                else:
                    update_repos.add(repo)
                    if logging == 1:
                        print('[DEL][DRY] {}; {}; {}'.format(repo, label, labels[label]))
        elif logging == 1:
            error(0, '[LBL][ERR] {}; {} - {}'.format(repo, code, response.json()['message']))
            errors += 1
        elif logging == 0 or logging == 3:
            error(0, 'ERROR: LBL; {}; {} - {}'.format(repo, code, response.json()['message']))
            errors += 1
    if errors > 0:
        if logging == 1:
            error(10, '[SUMMARY] {} error(s) in total, please check log above'.format(errors))
        elif logging == 0 or logging == 3:
            error(10, 'SUMMARY: {} error(s) in total, please check log above'.format(errors))
        else:
            error(10)
    elif logging == 1:
        print('[SUMMARY] {} repo(s) updated successfully'.format(len(update_repos)))
    elif logging == 0 or logging == 3:
        print('SUMMARY: {} repo(s) updated successfully'.format(len(update_repos)))


def get_labels(template_repository, config):
    if template_repository:
        response, code = get_response('repos/{}/labels?per_page=100&page=1'.format(template_repository))
        if code == 200:
            return {label['name']: label['color'] for label in response.json()}
        else:
            error(10, response.json()['message'])
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
            error(10, response.json()['message'])
    elif 'repos' in config:
        return [repo for repo in config['repos'] if config['repos'].getboolean(repo)]
    else:
        error(7, 'No repositories specification has been found')


if __name__ == '__main__':
    cli(obj={})
