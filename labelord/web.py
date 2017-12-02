import flask
import os
import configparser
import json
from .helpers import *
from .github import *


class LabelordWeb(flask.Flask):
    '''
    Base Flask class.
    '''

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.lblconfig = None
        self.ghsession = None
        self.lastlabel = None
        self.lastaction = None


    def inject_session(self, session):
        '''
        Sets the session to be used for communication with GitHub.

        :param session: Session to be used.
        '''
        session.headers = {'User-Agent': 'mi-pyt-02-labelord'}
        github_token = self.lblconfig['github'].get('token', '')
        def token_auth(req):
            req.headers['Authorization'] = 'token ' + github_token
            return req
        session.auth = token_auth
        self.ghsession = session


    def reload_config(self):
        '''
        Reloads the configuration file.
        '''
        self.lblconfig = configparser.ConfigParser()
        self.lblconfig.optionxform = str
        configpath = os.getenv('LABELORD_CONFIG')
        if configpath is None:
            configpath = './config.cfg'
        self.lblconfig.read(configpath)
        check_config(self.lblconfig)


def create_app():
    '''
    Flask app builder, creates Flask app instance.

    :return: Flask app instance.
    '''
    app = LabelordWeb(__name__)
    app.lblconfig = configparser.ConfigParser()
    app.lblconfig.optionxform = str
    configpath = os.getenv('LABELORD_CONFIG')
    if configpath is None:
        configpath = './config.cfg'
    app.lblconfig.read(configpath)
    return app


def load_repos():
    '''
    Loads repositories from the configuration.

    :return: Array of full repositories names set up in configuration file.
    '''
    config = app.lblconfig
    return [repo for repo in config['repos'] if config['repos'].getboolean(repo)]


def check_request(request):
    '''
    Checks if incoming request is valid.

    :param request: Request to be checked.
    :return: True if request is valid, False otherwise.
    '''
    json_data = json.loads(request.data)
    repo = json_data['repository']['full_name']
    repos = load_repos()
    return repo in repos


def get():
    '''
    Method to be run after received GET request.
    '''
    repos = load_repos()
    return flask.make_response(flask.render_template('index.html', repos=repos), 200)


def post():
    '''
    Method to be run after received POST request.
    '''
    if not verify_signature(flask.request, app):
        return flask.make_response('UNAUTHORIZED', 401)
    elif not check_request(flask.request):
        return flask.make_response('BAD REQUEST', 400)
    if is_redundant(app):
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


def sync_labels(event, repos, label, color, old_label):
    '''
    Synchronizes defined repositories with given label.

    :param event: String describing event, can be *created*, *edited* or *deleted*.
    :param repos: Full repositories names that should be synchronized.
    :param label: Label name that should be synchronized.
    :param color: Label color that should be synchronized.
    :param old_label: Name of the old label that should be updated.
    '''
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


app = create_app()


@app.route('/', methods=['GET', 'POST'])
def respond():
    '''
    Flask respond method to requests.
    '''
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

