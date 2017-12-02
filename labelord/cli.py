import click
import configparser
import requests
from .web import *
from .helpers import *
from .github import *


@click.group('labelord')
@click.option('-c', '--config', default='./config.cfg', envvar='LABELORD_CONFIG', help='Configuration file path.')
@click.option('-t', '--token', envvar='GITHUB_TOKEN', default='', help='GitHub token.')
@click.version_option(version=0.5, prog_name='labelord')
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
    """Run labels processingpython -m pip install --extra-index-url https://test.pypi.org/pypi labelord_klememi1"""
    session = set_session()
    config = ctx.obj.get('config')
    template_repository = template_repo if template_repo else config.get('others', 'template-repo', fallback='')
    labels = get_labels(template_repository, config)
    repos = get_repos(all_repos, config)
    logging = 1 if verbose and not quiet else 2 if quiet and not verbose else 0
    perform_operation(True if mode == 'replace' else False, repos, labels, dry_run, logging, session)


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


def main():
    cli(obj={})
