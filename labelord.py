# MI-PYT, task 1 (requests+click)
# File: labelord.py
# TODO: add colorful option & refactoring!
import click
import requests
import configparser
import sys
import flask
import os
import hashlib
import hmac
import json


@click.group('labelord')
@click.option('-c', '--config', default='./config.cfg', envvar='LABELORD_CONFIG', help='Configuration file path.')
@click.option('-t', '--token', envvar='GITHUB_TOKEN', default='', help='GitHub token.')
@click.version_option(version=0.1, prog_name='labelord')
@click.pass_context
def cli(ctx, config, token):
    cfg = configparser.ConfigParser()
    cfg.optionxform = str
    cfg.read(config)
    cfgtoken = cfg.get('github', 'token', fallback='')
    ctx.obj['token'] = token if token else cfgtoken
    ctx.obj['config'] = cfg
    ctx.obj['configpath'] = config


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
            if len(response.json()) < 100:
                break
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
            if len(response.json()) < 100:
                break
            page += 1
            response, code = get_response('repos/{}/labels?per_page=100&page={}'.format(reposlug, page))
    elif code == 404:
        error(5, 'GitHub: ERROR {} - {}'.format('404', response.json().get('message', '')))
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
    session = set_session()
    config = ctx.obj.get('config')
    template_repository = template_repo if template_repo else config.get('others', 'template-repo', fallback='')
    labels = get_labels(template_repository, config)
    repos = get_repos(all_repos, config)
    logging = 1 if verbose and not quiet else 2 if quiet and not verbose else 0
    perform_operation(True if mode == 'replace' else False, repos, labels, dry_run, logging, session)


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
    return session


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
        error(4, 'GitHub: ERROR {} - {}'.format(response.status_code, response.json().get('message', '')))
    return response, response.status_code


def update_label(session, repo, label, data):
    # session = ctx.obj.get('session', requests.Session())
    response = session.patch('https://api.github.com/repos/{}/labels/{}'.format(repo, label), json=data)
    if response.status_code == 200:
        return response.status_code, None
    return response.status_code, response.json().get('message', '')


def add_label(session, repo, data):
    # session = ctx.obj.get('session', requests.Session())
    response = session.post('https://api.github.com/repos/{}/labels'.format(repo), json=data)
    if response.status_code == 201:
        return response.status_code, None
    return response.status_code, response.json().get('message', '')


def delete_label(session, repo, label):
    # session = ctx.obj.get('session', requests.Session())
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
######################################################################
######################################################################
class LabelordWeb(flask.Flask):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.lblconfig = None
        self.ghsession = None
        self.lastlabel = None
        self.lastaction = None


    def inject_session(self, session):
        session.headers = {'User-Agent': 'mi-pyt-02-labelord'}
        github_token = self.lblconfig['github'].get('token', '')
        def token_auth(req):
            req.headers['Authorization'] = 'token ' + github_token
            return req
        session.auth = token_auth
        self.ghsession = session


    def reload_config(self):
        self.lblconfig = configparser.ConfigParser()
        self.lblconfig.optionxform = str
        configpath = os.getenv('LABELORD_CONFIG')
        if configpath is None:
            configpath = './config.cfg'
        self.lblconfig.read(configpath)
        check_config(self.lblconfig)


def check_config(lblconfig):
    token = lblconfig.get('github', 'token', fallback='')
    webhook_secret = lblconfig.get('github', 'webhook_secret', fallback='')
    if not webhook_secret:
        error(8, 'No webhook secret has been provided')
    elif not 'repos' in lblconfig:
        error(7, 'No repositories specification has been found')
    elif not token:
        error(3, 'No GitHub token has been provided')


def create_app():
    app = LabelordWeb(__name__)
    app.lblconfig = configparser.ConfigParser()
    app.lblconfig.optionxform = str
    configpath = os.getenv('LABELORD_CONFIG')
    if configpath is None:
        configpath = './config.cfg'
    app.lblconfig.read(configpath)
    return app


app = create_app()


def load_repos():
    config = app.lblconfig
    return [repo for repo in config['repos'] if config['repos'].getboolean(repo)]


def verify_signature(request):
    secret = app.lblconfig.get('github', 'webhook_secret', fallback='')
    request_signature = request.headers.get('X-Hub-Signature', '')
    if not request_signature:
        return False
    signature = hmac.new(bytes(secret, 'UTF-8'), msg=request.data, digestmod='sha1').hexdigest()
    return hmac.compare_digest('sha1=' + signature, request_signature)


def check_request(request):
    json_data = json.loads(request.data)
    repo = json_data['repository']['full_name']
    repos = load_repos()
    return repo in repos


def get():
    repos = load_repos()
    return flask.make_response(flask.render_template('index.html', repos=repos), 200)


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


def post():
    if not verify_signature(flask.request):
        return flask.make_response('UNAUTHORIZED', 401)
    elif not check_request(flask.request):
        return flask.make_response('BAD REQUEST', 400)
    if is_redundant():
        return flask.make_response('OK', 200)
    repos = load_repos()
    json_data = json.loads(flask.request.data)
    original_repo = json_data['repository']['full_name']
    event = json_data['action']
    todo_repos = list(filter(lambda x: x != original_repo, repos))
    label = json_data['label']['name']
    color = json_data['label']['color']
    old_label = ''
    if event == 'edited' and json_data.get('changes', '').get('name', ''):
        old_label = json_data.get('changes', '').get('name', '').get('from', '')
    else:
        old_label = label
    return sync_labels(event, todo_repos, label, color, old_label)


def is_redundant():
    json_data = json.loads(flask.request.data)
    new_action = json_data['action']
    new_label = json_data['label']['name']
    if (new_label != app.lastlabel) or (new_action != app.lastaction):
        app.lastlabel = new_label
        app.lastaction = new_action
        return False
    return True


@app.route('/', methods=['GET', 'POST'])
def respond():
    if flask.request.method == 'GET':
        return get()
    elif flask.request.method == 'POST':
        event = flask.request.headers.get('X-Github-Event', '')
        if event == 'ping':
            return flask.make_response('OK', 200)
        elif event == 'label':
            return post()
        else:
            return flask.make_response('BAD REQUEST', 400)
    else:
        return flask.make_response('BAD REQUEST', 400)


@cli.command()
@click.pass_context
@click.option('--host', '-h', default='127.0.0.1', help='Hostname.')
@click.option('--port', '-p', default=5000, help='Port.')
@click.option('--debug', '-d', is_flag=True, envvar='FLASK_DEBUG', help='Debug mode.')
def run_server(ctx, host, port, debug):
    """Start local server app"""
    app.lblconfig = ctx.obj['config']
    # app.ghsession = ctx.obj['session']
    check_config(app.lblconfig)
    app.run(host=host, port=port, debug=debug)
#######################################################################
#######################################################################
if __name__ == '__main__':
    cli(obj={})
