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
@click.pass_context
def cli(ctx, config, token):
    # TODO: Add and process required app-wide options
    # You can/should use context 'ctx' for passing
    # data and objects to commands
    cfg = configparser.ConfigParser()
    cfg.read(config)
    cfgtoken = cfg.get('github', 'token', fallback='')
    github_token = token if token else cfgtoken
    if not github_token:
        error('No GitHub token has been provided')
        sys.exit(3)
    ctx.obj['token'] = github_token
    ctx.obj['session'] = requests.Session()
    session = ctx.obj.get('session')
    session.headers = {'User-Agent': 'mi-pyt-01-labelord'}
    def token_auth(req):
        req.headers['Authorization'] = 'token ' + github_token
        return req
    session.auth = token_auth


def error(*args, **kwargs):
    print(*args, file=sys.stderr, **kwargs)


@cli.command()
@click.pass_context
def list_repos(ctx):
    session = ctx.obj.get('session')
    response = session.get('https://api.github.com/user/repos?per_page=100&page=1')
    if response.status_code == 200:
        for repo in response.json():
            print(repo['full_name'])
    elif response.status_code == 401:
        error(response.json()['message'])
        sys.exit(4)
    else:
        sys.exit(10)


@cli.command()
@click.argument('reposlug')
@click.pass_context
def list_labels(ctx, reposlug):
    # TODO: Add required options/arguments
    # TODO: Implement the 'list_labels' command
    session = ctx.obj.get('session')
    response = session.get('https://api.github.com/repos/{}/labels?per_page=100&page=1'.format(reposlug))
    if response.status_code == 200:
        for label in response.json():
            print('#{} {}'.format(label['color'], label['name']))
    elif response.status_code == 404:
        error(response.json()['message'])
        sys.exit(5)
    else:
        sys.exit(10)


@cli.command()
@click.pass_context
def run(ctx):
    # TODO: Add required options/arguments
    # TODO: Implement the 'run' command
    ...


if __name__ == '__main__':
    cli(obj={})
