# This is skeleton for labelord module
# MI-PYT, task 1 (requests+click)
# File: labelord.py
# TODO: create requirements.txt and install
import click
import requests
import configparser
import sys
# Structure your implementation as you want (OOP, FP, ...)
# Try to make it DRY also for your own good


@click.group('labelord')
@click.option('-c', '--config', default='./config.cfg', help='Configuration file path.')
@click.option('-t', '--token', envvar='GITHUB_TOKEN', default='', help='GitHub token.')
@click.option('-y', '--colorful', is_flag=True, help='Turns on colors for logs.')
@click.version_option(version=0.1, prog_name='labelord')
@click.pass_context
def cli(ctx, config, token, colorful):
    # TODO: Add and process required app-wide options
    # You can/should use context 'ctx' for passing
    # data and objects to commands
    cfg = configparser.ConfigParser()
    cfg.optionxform = str
    cfg.read(config)
    cfgtoken = cfg.get('github', 'token', fallback='')
    github_token = token if token else cfgtoken
    if not github_token:
        error(3, 'No GitHub token has been provided')
    ctx.obj['token'] = github_token
    ctx.obj['session'] = requests.Session()
    ctx.obj['colorful'] = colorful
    ctx.obj['config'] = cfg
    set_session()


@click.pass_context
def set_session(ctx):
    session = requests.Session()
    session = ctx.obj.get('session')
    session.headers = {'User-Agent': 'mi-pyt-01-labelord'}
    def token_auth(req):
        req.headers['Authorization'] = 'token ' + ctx.obj.get('token')
        return req
    session.auth = token_auth
    ctx.obj['session'] = session


def error(return_value, *args, **kwargs):
    if args:
        print(*args, file=sys.stderr, **kwargs)
    sys.exit(return_value)


@click.pass_context
def get_response(ctx, uri):
    session = ctx.obj.get('session')
    response = session.get('https://api.github.com/' + uri)
    return response, response.status_code


@cli.command()
@click.pass_context
def list_repos(ctx):
    response, code = get_response('user/repos?per_page=100&page=1')
    if code == 200:
        for repo in response.json():
            print(repo['full_name'])
    elif code == 404:
        error(4, response.json()['message'])
    else:
        error(10)


@cli.command()
@click.argument('reposlug')
@click.pass_context
def list_labels(ctx, reposlug):
    response, code = get_response('repos/{}/labels?per_page=100&page=1'.format(reposlug))
    if code == 200:
        for label in response.json():
            print('#{} {}'.format(label['color'], label['name']))
    elif code == 404:
        error(5, response.json()['message'])
    else:
        error(10)


@cli.command()
@click.argument('mode', type=click.Choice(['update', 'replace']))
@click.option('-a', '--all-repos', is_flag=True, help='Use all accessible repositories.')
@click.option('-d', '--dry-run', is_flag=True, help='Doesn\'t make any changes to GitHub, just prints them.')
@click.option('-v', '--verbose', is_flag=True, help='Turns on logs on standard output.')
@click.option('-q', '--quiet', is_flag=True, help='Turns off all logs.')
@click.option('-r', '--template-repo', default='', help='Repository to use as a template.')
@click.pass_context
def run(ctx, mode, all_repos, dry_run, verbose, quiet, template_repo):
    config = ctx.obj.get('config')
    template_repository = template_repo if template_repo else config.get('others', 'template-repo', fallback='')
    labels = get_labels(template_repository, config)
    repos = get_repos(all_repos, config)
    


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
