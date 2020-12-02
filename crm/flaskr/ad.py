import uuid

import requests
from flask import session, render_template, redirect, url_for, Blueprint, request
import msal
import flaskr.app_config as app_config
from json import loads
from datetime import datetime, timedelta

bp = Blueprint('ad', __name__)

def tokenExpired():
    start = datetime.strptime(session['start'], '%h %d %H:%M:%S')
    return (datetime.now() - start > timedelta(hours=1))

@bp.route("/")
def index():
    print('\n\n\n'+session.get('user', 'no user found')+'\n\n\n')
    if not session.get("user"):
        return redirect(url_for("ad.login"))
    return render_template('index.html', user=session["user"], version=msal.__version__, active='home')

@bp.route('/token')
def token():
    return session.get('token', 'No token found')

@bp.route("/login")
def login():
    session["state"] = str(uuid.uuid4())
    # Technically we could use empty list [] as scopes to do just sign in,
    # here we choose to also collect end user consent upfront
    auth_url = build_auth_url(scopes=app_config.SCOPE, state=session["state"])
    print(auth_url)
    if 'redirect' in request.args:
        redir = request.args.get('redirect')
        session['redirect'] = redir
        print('\n\nSetting redirect to {}\n\n'.format(redir))
    return render_template("login.html", auth_url=auth_url, version=msal.__version__)


@bp.route(app_config.REDIRECT_PATH)  # Its absolute URL must match your app's redirect_uri set in AAD
def authorized():
    if request.args.get('state') != session.get("state"):
        return redirect(url_for("ad.index"))  # No-OP. Goes back to Index page
    if "error" in request.args:  # Authentication/Authorization failure
        return render_template("auth_error.html", result=request.args)
    if request.args.get('code'):
        cache = _load_cache()
        result = _build_msal_app(cache=cache).acquire_token_by_authorization_code(
            request.args['code'],
            scopes=app_config.SCOPE,  # Misspelled scope would cause an HTTP 400 error here
            redirect_uri=url_for("ad.authorized", _external=True))
        if "error" in result:
            return render_template("auth_error.html", result=result)
        claims = result.get("id_token_claims")
        name = claims['name'].split(', ')
        try:
            session["user"] = name[1] + ' ' + name[0]
        except IndexError:
            session["user"] = claims['name']
        session['start'] = datetime.now().strftime('%h %d %H:%M:%S')
        session['email'] = claims['preferred_username']
        token_cache = loads(cache.serialize())
        if 'AccessToken' in token_cache and len(token_cache['AccessToken']) == 1:
            for key in token_cache['AccessToken']:
                session['token'] = token_cache['AccessToken'][key]['secret']
                from json import dump
                dump(result.get('id_token_claims'), open('CLAIMS.json', 'w'), indent=4)
    if 'redirect' in session:
        return redirect(session.pop('redirect'))
    return redirect(url_for("ad.index"))


@bp.route("/logout")
def logout():
    session.clear()  # Wipe out user and its token cache from session
    return redirect(  # Also logout from your tenant's web session
        app_config.AUTHORITY + "/oauth2/v2.0/logout" +
        "?post_logout_redirect_uri=" + url_for("ad.index", _external=True))


#
@bp.route("/graphcall")
def graphcall():
    token = _get_token_from_cache(app_config.SCOPE)
    if not token:
        return redirect(url_for("ad.login"))
    graph_data = requests.get(  # Use token to call downstream service
        app_config.ENDPOINT,
        headers={'Authorization': 'Bearer ' + token['access_token']},
    ).json()
    print(token['access_token'])
    return render_template('display.html', result=graph_data)


def _load_cache():
    cache = msal.SerializableTokenCache()
    if session.get("token_cache"):
        cache.deserialize(session["token_cache"])
    return cache


def _save_cache(cache):
    if cache.has_state_changed:
        session["token_cache"] = cache.serialize()
        token_cache = loads(session['token_cache'])
        if 'AccessToken' in token_cache and len(token_cache['AccessToken']) == 1:
            for key in token_cache['AccessToken']:
                session['token'] = token_cache['AccessToken'][key]['secret']
        print(session['token'])


def _build_msal_app(cache=None, authority=None):
    return msal.ConfidentialClientApplication(
        app_config.CLIENT_ID, authority=authority or app_config.AUTHORITY,
        client_credential=app_config.CLIENT_SECRET, token_cache=cache)


def build_auth_url(authority=None, scopes=None, state=None):
    return _build_msal_app(authority=authority).get_authorization_request_url(
        scopes or [],
        state=state or str(uuid.uuid4()),
        redirect_uri=url_for("ad.authorized", _external=True))


def _get_token_from_cache(scope=None):
    cache = _load_cache()  # This web app maintains one cache per session
    cca = _build_msal_app(cache=cache)
    accounts = cca.get_accounts()
    if accounts:  # So all account(s) belong to the current signed-in user
        result = cca.acquire_token_silent(scope, account=accounts[0])
        _save_cache(cache)
        return result
