from django.contrib import messages
from django.shortcuts import render, redirect, reverse

import httpx

from connector.oidc import provider_discovery, client_registration, make_random_string

# Create your views here.


def connect_oidc(request):
    context = {}
    if request.method == 'POST':
        print(request.POST)
        issuer_url = request.POST.get('issuer_url').strip()
        context['issuer_url'] = issuer_url
        print(issuer_url)
        if issuer_url[-1] != '/':
            issuer_url = issuer_url + '/'
        #try:
        r = httpx.get(issuer_url)
        provider_info, valid = provider_discovery(issuer_url)
        print(provider_info)
        if valid:
            registration_endpoint = provider_info['registration_endpoint']
            state = make_random_string()
            request.session['state_session'] = {
                'provider_info': provider_info,
                'state': state
            }
            session_updt, query = client_registration(state=state, registration_endpoint=registration_endpoint)
            if session_updt:
                # request.session['state_session']['client_id'] = session_updt.get('client_id')
                # request.session['state_session']['client_secret'] = session_updt.get('client_secret')
                # request.session['state_session']['code_verifier'] = session_updt.get('code_verifier')
                # request.session['state_session']['redirect_view'] = reverse('pod_session:pod')
                authorization_endpoint = provider_info['authorization_endpoint']
                auth_query = authorization_endpoint + query

                for x, y in request.session.items():
                    print(x, y)

                return redirect(auth_query)
            else:
                messages.error(request, f"Error: {query}")
        else:
            messages.error(request,f"Invalid issuer. {provider_info}")
        # except:
        #     messages.error(request,f"Invalid URL. Please, try again or check the address.")
    elif request.method == 'GET':
        pass
    return render(request,'index.html', context)


def pod(request):
    context = {
        'session': request.session.get('state_session')
    }
    return render(request,'pod_session/view_resource.html', context)
