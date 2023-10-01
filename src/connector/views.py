from django.conf import settings
from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect, HttpResponseRedirect, HttpResponse, reverse
from django.utils import timezone
from django.views.decorators.http import require_http_methods

from datetime import datetime, timedelta

import jwcrypto
import pytz
import requests

from connector.utillities.snippets import make_random_string
from connector.oidc import make_token_for, get_web_id, client_registration

from pods.models import StateSession, OpenIDprovider


_OID_CALLBACK_URI = settings.OID_CALLBACK_URI
_CLIENT_NAME = settings.CLIENT_NAME
_CLIENT_CONTACT = settings.CLIENT_CONTACT
_CLIENT_URL = settings.CLIENT_URL


# Create your views here.

# @require_http_methods(["POST"])
# def connect_webid(request):
#     pk = request.POST.get('session_id')
#     state_session = get_object_or_404(StateSession, pk=pk)
#     if state_session.is_active:
#         request.session['web_id'] = state_session.webid
#         request.session['session_pk'] = state_session.pk
#         return redirect('pods:dashboard')
#     else:
#         refresh_token_query = state_session.refresh_token_query(redirect_view=reverse('pods:dashboard'))
#         return redirect(refresh_token_query)


def connect_webid(request, pk):
    # pk = request.POST.get('session_id')
    state_session = get_object_or_404(StateSession, pk=pk)
    if state_session.is_active:
        request.session['web_id'] = state_session.webid
        request.session['session_pk'] = state_session.pk
        return redirect('pods:dashboard')
    else:
        refresh_token_query = state_session.refresh_token_query(redirect_view=reverse('pods:dashboard'))
        return redirect(refresh_token_query)


def disconnect_webid(request):
    request.session['web_id'] = None
    request.session['session_pk'] = None

    return redirect('pods:dashboard')


def connect_oidc(request):
    if request.method == 'POST':
        pk = request.POST.get('oidcp')

        op = get_object_or_404(OpenIDprovider, pk=pk)
        state = make_random_string()
        state_session = StateSession(
            state=state,
            user=request.user,
            redirect_view=reverse('pods:dashboard'),
            oicdp=op
        )
        state_session.save()

        authorization_endpoint = op.provider_info['authorization_endpoint']
    elif request.method == 'GET':
        pk = request.GET.get('session_pk')
        state_session = get_object_or_404(StateSession, pk=pk)
        authorization_endpoint = state_session.oicdp.provider_info['authorization_endpoint']
    valid, query = client_registration(state_session=state_session)
    if valid:
        auth_query = authorization_endpoint + query
        return redirect(auth_query)
    else:
        if state_session.client_id == "" or state_session.client_id is None:
            state_session.delete()
        messages.error(request, f"Error: {query}")
        return redirect('pods:dashboard')


def oauth_callback(request):
    auth_code = request.GET.get('code', None)
    state = request.GET.get('state', None)
    state_session = get_object_or_404(StateSession, state=state)

    provider_info = state_session.oicdp.provider_info
    # Generate a key-pair.
    keypair = jwcrypto.jwk.JWK.generate(kty='EC', crv='P-256')
    # Exchange auth code for access token
    resp = requests.post(url=provider_info['token_endpoint'],
                         data={
                             "grant_type": "authorization_code",
                             "client_id": state_session.client_id,
                             "client_secret": state_session.client_secret,
                             "redirect_uri": _OID_CALLBACK_URI,
                             "code": auth_code,
                             "code_verifier": state_session.code_verifier,
                         },
                         headers={
                             'content-type': 'application/x-www-form-urlencoded',
                             'DPoP':  make_token_for(keypair, provider_info['token_endpoint'], 'POST')
                         },
                         allow_redirects=False)
    print(f'callback rest: {resp}')
    # update state_session
    if resp.status_code == 200:
        result = resp.json()
        # update state_session with tokens from the exchange
        at = result.get('access_token')
        web_id = get_web_id(at)
        state_session.access_token = at
        state_session.id_token = result.get('id_token')
        state_session.DPoP_key = keypair.export()
        state_session.webid = web_id
        expires_at = datetime.utcnow() + timedelta(seconds=result.get('expires_in'))
        state_session.expires_at = timezone.make_aware(expires_at, pytz.UTC, True)
        state_session.token_type = result.get('token_type')
        state_session.refresh_token = result.get('refresh_token')
        state_session.save()
        request.session['web_id'] = web_id
        request.session['session_pk'] = state_session.pk
    else:
        if state_session.access_token == "" or state_session.access_token is None:
            state_session.delete()
        try:
            # api response
            result = resp.json()  # api response
            name = result.get('name')
            message = result.get('message')
            description = result.get('error_description')
            error = result.get('error')
            request.session['web_id'] = None
            request.session['session_pk'] = None
            messages.error(request, f"Error: {error} {name} {message} {description}")
        except:
            # web server response
            messages.error(request, resp.text)

    return HttpResponseRedirect(state_session.redirect_view)


def refresh_token(request):
    session_pk = request.GET.get('session_pk')
    redirect_uri = request.GET.get('redirect_uri')
    state_session = get_object_or_404(StateSession, pk=session_pk)
    if state_session.is_active:
        request.session['web_id'] = state_session.webid
        request.session['session_pk'] = state_session.pk
    else:
        provider_info = state_session.oicdp.provider_info
        # Generate a key-pair.
        keypair = jwcrypto.jwk.JWK.generate(kty='EC', crv='P-256')

        # Exchange auth code for access token
        resp = requests.post(url=provider_info['token_endpoint'],
                             data={
                                 "grant_type": "refresh_token",
                                 "client_id": state_session.client_id,
                                 "client_secret": state_session.client_secret,
                                 'refresh_token': state_session.refresh_token,
                             },
                             headers={
                                 'content-type': 'application/x-www-form-urlencoded',
                                 'DPoP':  make_token_for( keypair, provider_info['token_endpoint'], 'POST')
                             },
                             allow_redirects=False)
        # update state_session
        if resp.status_code == 200:
            result = resp.json()
            # update state_session with tokens from the exchange
            at = result.get('access_token')
            web_id = get_web_id(at)

            state_session.access_token = at
            state_session.id_token = result.get('id_token')
            state_session.DPoP_key = keypair.export()
            state_session.web_id = web_id
            expires_at = datetime.utcnow() + timedelta(seconds=result.get('expires_in'))
            state_session.expires_at = timezone.make_aware(expires_at, pytz.UTC, True)
            state_session.token_type = result.get('token_type')
            state_session.refresh_token = result.get('refresh_token')
            state_session.save()
            request.session['web_id'] = web_id
            request.session['session_pk'] = state_session.pk
        else:
            try:
                # api response
                result = resp.json()  # api response
                if resp.status_code == 400 and result.get("error") == "invalid_grant":
                    connect_url = reverse('connector:connect')
                    return redirect(f'{connect_url}?session_pk={state_session.pk}')
                name = result.get('name')
                message = result.get('message')
                description = result.get('error_description')
                error = result.get('error')
                request.session['web_id'] = None
                request.session['session_pk'] = None
                messages.error(request, f"Error: {error} {name} {message} {description}")
            except:
                # web server response
                messages.error(request, resp.text)

    return redirect(redirect_uri)  # request
