# This is skeleton for labelord module
# MI-PYT, task 1 (requests+click)
# File: labelord.py
# TODO: create requirements.txt and install
import click
import requests
import configparser
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
    cfgparser = configparser.ConfigParser()
    cfgparser.read(config)
    github_token = token if token else cfgparser['github']['token']
    # Use this session for communication with GitHub
    ctx.obj['token'] = github_token
    ctx.obj['session'] = requests.Session()
    session = ctx.obj.get('session')
    session.headers = {'User-Agent': 'mi-pyt-01-labelord'}
    session.auth = token_auth


@click.pass_context
def token_auth(ctx, req):
    req.headers['Authorization'] = 'token ' + ctx.obj.get('token')
    return req


@cli.command()
@click.pass_context
def list_repos(ctx):
    # TODO: Add required options/arguments
    # TODO: Implement the 'list_repos' command
    session = ctx.obj.get('session')
    r = session.get('https://api.github.com/user/repos?per_page=100&page=1')
    print(r.status_code)
    for i in r.json():
        print(i['full_name'])


@cli.command()
@click.pass_context
def list_labels(ctx):
    # TODO: Add required options/arguments
    # TODO: Implement the 'list_labels' command
    ...


@cli.command()
@click.pass_context
def run(ctx):
    # TODO: Add required options/arguments
    # TODO: Implement the 'run' command
    ...


if __name__ == '__main__':
    cli(obj={})
