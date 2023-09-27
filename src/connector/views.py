from django.conf import settings
from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect, HttpResponseRedirect, HttpResponse, reverse
from django.utils import timezone

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

def connect_webid(request):
    print(request.POST)
    pk = request.POST.get('session_id')
    s = get_object_or_404(StateSession, pk=pk)

    return redirect(s.refresh_token_url)
    # return HttpResponse(f'connect_webid {s.webid}')


def connect_oidc(request):
    print(request.POST)
    pk = request.POST.get('oidcp')
    op = get_object_or_404(OpenIDprovider, pk=pk)
    state = make_random_string()
    print(reverse('pods:dashboard'))
    state_session = StateSession(
        state=state,
        user=request.user,
        redirect_view=reverse('pods:dashboard'),
        oicdp=op
    )
    state_session.save()
    query = client_registration(state_session=state_session)
    print(query)
    auth_query = op.provider_info['authorization_endpoint'] + query
    print(auth_query)
    return redirect(auth_query)


def oauth_callback(request):
    print("oauth")
    print(f'request.user: {request.user}')
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

    result = resp.json()
    print(f'OAUTH resp code : {resp.status_code }')
    print(f"result: {result}")
    # update state_session
    if resp.status_code == 200:
        # update state_session with tokens from the exchange
        at = result.get('access_token')
        web_id = get_web_id(at)
        print(f'web_id: {web_id}')
        # w, created = WebID.objects.get_or_create(
        #     webid=web_id,
        #     provider=state_session.oicdp,
        #     user=state_session.user
        # )
        # state_session.webid = get_web_id(at)
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
        name = result.get('name')
        message = result.get('message')
        description = result.get('error_description')
        error = result.get('error')
        messages.warning(request, f"Error: {error} {name} {message} {description}")
    return HttpResponseRedirect(state_session.redirect_view)


def refresh_token(request, state_session):
    print("refresh_token")
    # state_session = get_object_or_404(StateSession, pk=pk)
    if state_session.is_active:
        print('active')
        request.session['web_id'] = state_session.webid
        request.session['session_pk'] = state_session.pk
    else:
        print('expired')
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
        result = resp.json()
        # update state_session
        if resp.status_code == 200:
            # update state_session with tokens from the exchange
            at = result.get('access_token')
            web_id = get_web_id(at)
            print(f'web_id: {web_id}')

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
            print(web_id)
        else:
            name = result.get('name')
            message = result.get('message')
            description = result.get('error_description')
            error = result.get('error')
            request.session['web_id'] = f"Error: {error} {name} {message} {description}"
            messages.warning(request, f"Error: {error} {name} {message} {description}")

    return request  # HttpResponseRedirect(state_session.redirect_view)
