from django.conf import settings
from django.contrib import messages
from django.forms.models import model_to_dict
from django.shortcuts import get_object_or_404, redirect, HttpResponseRedirect, reverse, render
from django.utils import timezone

from datetime import datetime, timedelta

import httpx
import jwcrypto
import pytz
import requests

from connector.oidc import (make_token_for,
                            get_web_id,
                            client_registration,
                            make_random_string,
                            provider_discovery
                            )

from pod_registration.models import StateSession, OpenIDprovider


_OID_CALLBACK_URI = settings.OID_CALLBACK_URI
_CLIENT_NAME = settings.CLIENT_NAME
_CLIENT_CONTACT = settings.CLIENT_CONTACT
_CLIENT_URL = settings.CLIENT_URL


# Create your views here.


def connect_webid(request, pk):
    # pk = request.POST.get('session_id')
    state_session = get_object_or_404(StateSession, pk=pk)
    if state_session.is_active:
        request.session['web_id'] = state_session.webid
        request.session['session_pk'] = state_session.pk
        return redirect('pod_registration:dashboard')
    else:
        refresh_token_query = state_session.refresh_token_query(redirect_view=reverse('pod_registration:dashboard'))
        return redirect(refresh_token_query)


def disconnect_webid(request):
    request.session['web_id'] = None
    request.session['session_pk'] = None
    return redirect('pod_registration:dashboard')


def disconnect_session(request):
    request.session['state_session'] = None
    return redirect('home')


def connect_oidc(request):
    if request.method == 'POST':
        pk = request.POST.get('oidcp')

        op = get_object_or_404(OpenIDprovider, pk=pk)
        state = make_random_string()
        state_session = StateSession(
            state=state,
            user=request.user,
            redirect_view=reverse('pod_registration:dashboard'),
            oicdp=op
        )
        state_session.save()

        authorization_endpoint = op.provider_info['authorization_endpoint']
    else:
        pk = request.GET.get('session_pk')
        state_session = get_object_or_404(StateSession, pk=pk)
        authorization_endpoint = state_session.oicdp.provider_info['authorization_endpoint']

    # valid, query = client_registration(state_session=state_session)
    session_updt, query = client_registration(state=state_session.state,
                                              registration_endpoint=state_session.oicdp.provider_info['registration_endpoint'])
    if session_updt:
        state_session.client_id = session_updt.get('client_id')
        state_session.client_secret = session_updt.get('client_secret')
        state_session.code_verifier = session_updt.get('code_verifier')
        state_session.save()
        auth_query = authorization_endpoint + query
        return redirect(auth_query)
    else:
        if state_session.client_id == "" or state_session.client_id is None:
            state_session.delete()
        messages.error(request, f"Error: {query}", extra_tags='html_safe')
        return redirect('pod_registration:dashboard')


def connect_oidc_session(request):
    context = {}
    if request.method == 'POST':
        print('connect_oidc_session')
        issuer_url = request.POST.get('issuer_url').strip()
        context['issuer_url'] = issuer_url
        if issuer_url[-1] != '/':
            issuer_url = issuer_url + '/'
        try:
            r = httpx.get(issuer_url)
            provider_info, valid = provider_discovery(issuer_url)
            if valid:
                registration_endpoint = provider_info['registration_endpoint']
                state = make_random_string()
                session_updt, query = client_registration(state=state, registration_endpoint=registration_endpoint)
                if session_updt:
                    request.session['state_session'] = {
                        'token_endpoint': provider_info['token_endpoint'],
                        'state': state,
                        'redirect_view': reverse('pod_session:resource_form'),
                        **session_updt
                    }
                    authorization_endpoint = provider_info['authorization_endpoint']
                    auth_query = authorization_endpoint + query
                    return redirect(auth_query)
                else:
                    messages.error(request, f"Error: {query}", extra_tags='html_safe')
            else:
                messages.error(request,f"Invalid issuer. {provider_info}")
        except:
            messages.error(request,f"Invalid URL. Please, check the url and try again.")
    elif request.method == 'GET':
        pass
    return render(request,'index.html', context)


def oauth_callback(request):
    """
    Handles OAuth callback request
    :param request:
        GET request like:
        /connector/callback?code=XWSm3D3v4Bw-RPM7lbYo64AG26Em4Qs6TyuWVO4XNUW&state=tKTWNun0QH0LTpi4Fuc44uA82bsM9AYgpuB9lhItlHkhA1CKLPOpfA
    :return:
        HttpResponseRedirect to redirect_view
    """
    auth_code = request.GET.get('code', None)
    state = request.GET.get('state', None)
    state_session_obj = StateSession.objects.filter(state=state).first()  # if exists in db, then use pod registration model
    if state_session_obj:
        state_session = model_to_dict(state_session_obj)
        provider_info = state_session_obj.oicdp.provider_info
        token_endpoint = provider_info['token_endpoint']
        session_login = False
    else:
        state_session = request.session.get('state_session')  # previously set in connect_oidc_session
        token_endpoint = state_session['token_endpoint']
        session_login = True
    # Generate a key-pair.
    keypair = jwcrypto.jwk.JWK.generate(kty='EC', crv='P-256')
    # Exchange auth code for access token
    resp = requests.post(url=token_endpoint,
                         data={
                             "grant_type": "authorization_code",
                             "client_id": state_session['client_id'],
                             "client_secret": state_session['client_secret'],
                             "redirect_uri": _OID_CALLBACK_URI,
                             "code": auth_code,
                             "code_verifier": state_session['code_verifier'],
                         },
                         headers={
                             'content-type': 'application/x-www-form-urlencoded',
                             'DPoP': make_token_for(keypair, token_endpoint, 'POST')
                         },
                         allow_redirects=False)
    if resp.status_code == 200:
        # update state_session with tokens from the exchange and web_id
        if session_login:
            resp_json = resp.json()
            at = resp_json.get('access_token')
            web_id = get_web_id(at)
            state_session['access_token'] = at
            state_session['web_id'] = web_id
            expires_at = datetime.utcnow() + timedelta(seconds=resp_json.get('expires_in'))
            state_session['expires_at'] = timezone.make_aware(expires_at, pytz.UTC, True).timestamp()
            state_session['token_type'] = resp_json.get('token_type')
            state_session['refresh_token'] = resp_json.get('refresh_token')
            state_session['DPoP_key'] = keypair.export()
            request.session['state_session'] = state_session
            # request.session['aaa'] = 'aaa'  # dummy for request.session to be saved...
        else:
            web_id = _update_state_session(resp, state_session=state_session_obj, keypair=keypair)
            #TODO move session_pk and web_id to request.session['state_session'] like above
            request.session['session_pk'] = state_session_obj.pk
            request.session['web_id'] = web_id
    else:
        if state_session_obj.access_token == "" or state_session_obj.access_token is None:
            state_session_obj.delete()
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
            messages.error(request, resp.text, extra_tags='html_safe')
    return HttpResponseRedirect(state_session['redirect_view'])


def refresh_token(request):
    session_pk = request.GET.get('session_pk')
    redirect_uri = request.GET.get('redirect_uri')
    state_session_obj = get_object_or_404(StateSession, pk=session_pk)

    if state_session_obj.is_active:
        request.session['web_id'] = state_session_obj.webid
        request.session['session_pk'] = state_session_obj.pk
    else:
        provider_info = state_session_obj.oicdp.provider_info
        # Generate a key-pair.
        keypair = jwcrypto.jwk.JWK.generate(kty='EC', crv='P-256')
        # Exchange auth code for access token
        resp = requests.post(url=provider_info['token_endpoint'],
                             data={
                                 "grant_type": "refresh_token",
                                 "client_id": state_session_obj.client_id,
                                 "client_secret": state_session_obj.client_secret,
                                 'refresh_token': state_session_obj.refresh_token,
                             },
                             headers={
                                 'content-type': 'application/x-www-form-urlencoded',
                                 'DPoP':  make_token_for(keypair, provider_info['token_endpoint'], 'POST')
                             },
                             allow_redirects=False)
        # print(f'oauth_callback resp: {resp.json()}')

        # update state_session
        if resp.status_code == 200:
            # update state_session with tokens from the exchange
            web_id = _update_state_session(resp, state_session=state_session_obj, keypair=keypair)
            #TODO move session_pk and web_id to request.session['state_session'] like above
            request.session['session_pk'] = state_session_obj.pk
            request.session['web_id'] = web_id
        else:
            try:
                # api response
                result = resp.json()  # api response
                if resp.status_code == 400 and result.get("error") == "invalid_grant":
                    connect_url = reverse('connector:connect')
                    return redirect(f'{connect_url}?session_pk={state_session_obj.pk}')
                name = result.get('name')
                message = result.get('message')
                description = result.get('error_description')
                error = result.get('error')
                request.session['web_id'] = None
                request.session['session_pk'] = None
                messages.error(request, f"Error: {error} {name} {message} {description}")
            except:
                # web server response
                messages.error(request, resp.text, extra_tags='html_safe')

    return redirect(redirect_uri)  # request


def session_refresh_token(request):
    redirect_uri = request.GET.get('redirect_uri')
    state_session = request.session.get('state_session')  # previously set in connect_oidc_session
    token_endpoint = state_session['token_endpoint']
    # Generate a key-pair.
    keypair = jwcrypto.jwk.JWK.generate(kty='EC', crv='P-256')
    resp = requests.post(url=token_endpoint,
                         data={
                             "grant_type": "refresh_token",
                             "client_id": state_session['client_id'],
                             "client_secret": state_session['client_secret'],
                             'refresh_token': state_session['refresh_token'],
                         },
                         headers={
                             'content-type': 'application/x-www-form-urlencoded',
                             'DPoP':  make_token_for(keypair, 'token_endpoint', 'POST')
                         },
                         allow_redirects=False)

    # update state_session
    if resp.status_code == 200:
        resp_json = resp.json()
        at = resp_json.get('access_token')
        web_id = get_web_id(at)
        state_session['access_token'] = at
        state_session['web_id'] = web_id
        expires_at = datetime.utcnow() + timedelta(seconds=resp_json.get('expires_in'))
        state_session['expires_at'] = timezone.make_aware(expires_at, pytz.UTC, True).timestamp()
        state_session['token_type'] = resp_json.get('token_type')
        state_session['refresh_token'] = resp_json.get('refresh_token')
        state_session['DPoP_key'] = keypair.export()
        request.session['state_session'] = state_session
    else:
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
            messages.error(request, resp.text, extra_tags='html_safe')

    return redirect(redirect_uri)  # request


def _update_state_session(response, state_session, keypair) -> str:
    try:
        resp = response.json()
        # update state_session with tokens from the exchange
        at = resp.get('access_token')
        web_id = get_web_id(at)
        state_session.access_token = at
        state_session.id_token = resp.get('id_token')
        state_session.DPoP_key = keypair.export()
        state_session.webid = web_id
        expires_at = datetime.utcnow() + timedelta(seconds=resp.get('expires_in'))
        state_session.expires_at = timezone.make_aware(expires_at, pytz.UTC, True)
        state_session.token_type = resp.get('token_type')
        state_session.refresh_token = resp.get('refresh_token')
        state_session.save()
    except:
        web_id = None
    return web_id
