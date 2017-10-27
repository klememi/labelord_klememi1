import flask
import os
import configparser
import json
from .helpers import *
from .github import *


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


def create_app():
    app = LabelordWeb(__name__)
    app.lblconfig = configparser.ConfigParser()
    app.lblconfig.optionxform = str
    configpath = os.getenv('LABELORD_CONFIG')
    if configpath is None:
        configpath = './config.cfg'
    app.lblconfig.read(configpath)
    return app


def get():
    repos = load_repos(app)
    return flask.make_response(flask.render_template('index.html', repos=repos), 200)


def post():
    if not verify_signature(flask.request, app):
        return flask.make_response('UNAUTHORIZED', 401)
    elif not check_request(flask.request):
        return flask.make_response('BAD REQUEST', 400)
    if is_redundant(app):
        return flask.make_response('OK', 200)
    repos = load_repos(app)
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


app = create_app()


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
