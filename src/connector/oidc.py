from django.conf import settings

import base64
import hashlib
import httpx
import json
import os
import re

import jwcrypto
import jwcrypto.jwk
import jwcrypto.jws
import jwcrypto.jwt
import requests

from datetime import datetime
from oic.oic import Client
from oic.utils.authn.client import CLIENT_AUTHN_METHOD


_OID_CALLBACK_URI = settings.OID_CALLBACK_URI
_CLIENT_NAME = settings.CLIENT_NAME
_CLIENT_CONTACT = settings.CLIENT_CONTACT
_CLIENT_URL = settings.CLIENT_URL


def decode_access_token(access_token):
    return jwcrypto.jwt.JWT(jwt=access_token)


def get_headers(access_token, DPoP_key, lookup_url, method):
    keypair = jwcrypto.jwk.JWK.from_json(DPoP_key)
    return {
        'Authorization': ('DPoP ' + access_token),
        'DPoP': make_token_for(keypair, lookup_url,  method)
    }


def make_random_string():
    x = base64.urlsafe_b64encode(os.urandom(40)).decode('utf-8')
    x = re.sub('[^a-zA-Z0-9]+', '', x)
    return x


def make_verifier_challenge():
    code_verifier = make_random_string()
    code_challenge = hashlib.sha256(code_verifier.encode('utf-8')).digest()
    code_challenge = base64.urlsafe_b64encode(code_challenge).decode('utf-8')
    code_challenge = code_challenge.replace('=', '')
    return code_verifier, code_challenge


def make_token_for(keypair, uri, method):
    jwt = jwcrypto.jwt.JWT(header={
        "typ":
        "dpop+jwt",
        "alg":
        "ES256",
        "jwk":
        keypair.export(private_key=False, as_dict=True)
    },
                           claims={
                               "jti": make_random_string(),
                               "htm": method,
                               "htu": uri,
                               "iat": int(datetime.now().timestamp())
                           })
    jwt.make_signed_token(keypair)
    return jwt.serialize()


def get_web_id(access_token):
    decoded_access_token = jwcrypto.jwt.JWT(jwt=access_token)
    web_id = json.loads(
        decoded_access_token.token.objects['payload'])['sub']
    return web_id


def provider_discovery(provider_url):
    try:
        # Implement a Client with pyoidc: https://pyoidc.readthedocs.io/
        # 1) Issuer discovery using WebFinger and 2) Provider Info discovery
        u = provider_url + ".well-known/openid-configuration"
        resp = httpx.get(u)

    except requests.ConnectionError as e:
        return f'Connection Error. {str(e)}', False
    if resp.status_code == 200:
        provider_info = resp.json()
        return provider_info, True
    else:
        return f'Connection Error. {resp}', False


def client_registration(state_session=None):
    # 3) Client registration
    # https://pyoidc.readthedocs.io/en/latest/examples/rp.html#client-registration
    args = {
        "redirect_uris": [_OID_CALLBACK_URI],
        "contacts": [_CLIENT_CONTACT],
        "grant_types": ["refresh_token", "authorization_code", "client_credentials"],
        "client_name": _CLIENT_NAME
    }
    # registration_response = client.register(url='https://solid.lgalarno.ca/.oidc/reg', **args)
    client = Client(client_authn_method=CLIENT_AUTHN_METHOD)
    try:
        registration_response = client.register(
            state_session.oicdp.provider_info['registration_endpoint'],
            **args)
        # print(f"registration_response: {registration_response}")
        code_verifier, code_challenge = make_verifier_challenge()

        state_session.client_id = registration_response.get('client_id')
        state_session.client_secret = registration_response.get('client_secret')
        state_session.code_verifier = code_verifier
        state_session.save()
    except Exception as e:
        return False, e

    # 4) Authentication Request
    args = {
        "client_id": state_session.client_id,
        "response_type": "code",
        "code_challenge": code_challenge,
        "code_challenge_method": "S256",
        "scope": ["openid offline_access"],
        "redirect_uri": _OID_CALLBACK_URI,
        "state": state_session.state,
        "prompt": "consent",
    }
    auth_req = client.construct_AuthorizationRequest(request_args=args)
    query = auth_req.request(client.authorization_endpoint)
    return True, query
