import hashlib
import hmac
import requests
import json
import flask
import sys


def check_config(lblconfig):
    token = lblconfig.get('github', 'token', fallback='')
    webhook_secret = lblconfig.get('github', 'webhook_secret', fallback='')
    if not webhook_secret:
        error(8, 'No webhook secret has been provided')
    elif not 'repos' in lblconfig:
        error(7, 'No repositories specification has been found')
    elif not token:
        error(3, 'No GitHub token has been provided')


def verify_signature(request, app):
    secret = app.lblconfig.get('github', 'webhook_secret', fallback='')
    request_signature = request.headers.get('X-Hub-Signature', '')
    if not request_signature:
        return False
    signature = hmac.new(bytes(secret, 'UTF-8'), msg=request.data, digestmod='sha1').hexdigest()
    return hmac.compare_digest('sha1=' + signature, request_signature)


def is_redundant(app):
    json_data = json.loads(flask.request.data)
    new_action = json_data['action']
    new_label = json_data['label']['name']
    if (new_label != app.lastlabel) or (new_action != app.lastaction):
        app.lastlabel = new_label
        app.lastaction = new_action
        return False
    return True


def error(return_value, *args, **kwargs):
    if args:
        print(*args, file=sys.stderr, **kwargs)
    if return_value > 0:
        sys.exit(return_value)
