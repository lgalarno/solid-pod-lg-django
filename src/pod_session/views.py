from django.contrib import messages
from django.shortcuts import render, redirect, reverse, HttpResponse, get_object_or_404, HttpResponseRedirect
from django.views.decorators.http import require_http_methods

from pathlib import Path

import httpx

from connector.oidc import provider_discovery, client_registration, make_random_string, get_headers
from connector.solid_api import SolidAPI

from pod_session.utilities import is_session_active


# Create your views here.

def connect_oidc(request):
    context = {}
    if request.method == 'POST':
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
                        'provider_info': provider_info,
                        'state': state,
                        'redirect_view': reverse('pod_session:pod'),
                        **session_updt
                    }
                    authorization_endpoint = provider_info['authorization_endpoint']
                    auth_query = authorization_endpoint + query
                    return redirect(auth_query)
                else:
                    messages.error(request, f"Error: {query}")
            else:
                messages.error(request,f"Invalid issuer. {provider_info}")
        except:
            messages.error(request,f"Invalid URL. Please, check the url and try again.")
    elif request.method == 'GET':
        pass
    return render(request,'index.html', context)


def resource_form(request):
    state_session = request.session.get('state_session')
    context = {
        'title': 'resource-form',
        'session': state_session
    }
    return render(request, 'pod_session/resource_form.html', context)


#TODO update pod sessions for when the node.js api is down
def resource_view(request):
    resource_content = None
    state_session = request.session.get('state_session')
    if request.method == 'GET':
        resource_url = request.GET.get("url").strip()
    elif request.method == 'POST':
        resource_url = request.POST.get('resource_url').strip()
    context = {
        'title': 'view-resource',
        'resource_url': resource_url
    }
    if resource_url:
        if not is_session_active(state_session.get('expires_at')):
            redirect_view = reverse('pod_session:resource_view') + f'?url={resource_url}'
            refresh_token_view = reverse('connector:session-refresh-token')
            refresh_token_query = f'{refresh_token_view}?redirect_uri={redirect_view}'
            return redirect(refresh_token_query)
        headers = get_headers(access_token=state_session['access_token'],
                              DPoP_key=state_session['DPoP_key'],
                              url=resource_url,
                              method='GET')
        api = SolidAPI(headers=headers)  # , pod=pod.url)
        resp = api.get(url=resource_url)
        if resp.status_code == 401:
            messages.warning(request,
                             f"Got 401 trying to access {resource_url} . Please, log in to your pod provider before looking up for a resource")
        elif resp.status_code == 403:
            messages.warning(request,
                             f"403 Forbidden. Insufficient rights to a resource to access {resource_url}")
        elif resp.status_code != 200:
            messages.error(request, f"Error: {resp.status_code} {resp.text}")
        else:  # resp.status_code == 200
            resource_content = resp.text
            content_type = resp.headers.get('Content-Type')
            if 'text/turtle' in content_type:
                folder_data = api.read_folder_offline(url=resource_url, ttl=resource_content, pod=None)
                if folder_data:  # if folder_data is a container
                    for f in folder_data.folders:
                        f.view_url = reverse('pod_session:resource_view') + f'?url={f.url}'
                        f.del_url = reverse('pod_session:resource_delete') + f'?url={f.url}'
                    for f in folder_data.files:
                        f.view_url = reverse('pod_session:resource_view') + f'?url={f.url}'
                        f.del_url = reverse('pod_session:resource_delete') + f'?url={f.url}'
                    context['folder_data'] = folder_data
            else:  # content_type.startswith('application'):
                fn = Path(resource_url).name
                response = HttpResponse(
                    resp.content,
                    content_type=resp.headers.get('Content-Type'),
                    headers={f'Content-Disposition': f"attachment; filename = {fn}"},
                )
                return response
        context['resource_content'] = resource_content
        context['resource_url'] = resource_url
    return render(request,
                  'pod_session/resource_view.html',
                  context=context
                  )


@require_http_methods(["POST"])
def resource_create(request):
    state_session = request.session.get('state_session')
    resource_url = request.POST.get("resource_url")
    if not resource_url[-1] == '/':
        messages.warning(request,
                         f"You can't upload a file here. {resource_url} is not a container")
    else:
        fn = request.FILES['resource_to_pod'].name
        data = request.FILES['resource_to_pod'].read()
        new_resource_url = resource_url + fn
        if not is_session_active(state_session.get('expires_at')):
            redirect_view = reverse('pod_session:resource_view') + f'?url={resource_url}'
            refresh_token_view = reverse('connector:session-refresh-token')
            refresh_token_query = f'{refresh_token_view}?redirect_uri={redirect_view}'
            messages.warning(request,
                             f"Please, try again.")
            return redirect(refresh_token_query)
        headers = get_headers(access_token=state_session['access_token'],
                              DPoP_key=state_session['DPoP_key'],
                              url=resource_url,
                              method='POST')
        api = SolidAPI(headers=headers)
        resp = api.post_file(url=new_resource_url, content=data, content_type=request.FILES['resource_to_pod'].content_type)  #, headers=headers)
        if resp.status_code == 401:
            messages.warning(request,
                             f"Got 401 trying to post {new_resource_url} . You are not authorized to proceed.")
        elif resp.status_code != 201 and resp.status_code != 200:
            messages.warning(request, f"Error: {resp.status_code} {resp.text}")
        else:  # resp.status_code == 201:
            messages.success(request, f"{fn} uploaded to {resource_url}")
    view_url = reverse('pod_session:resource_view')
    return HttpResponseRedirect(f'{view_url}?url={resource_url}')


def resource_delete(request):
    state_session = request.session.get('state_session')
    resource_url = request.GET.get("url")
    redirect_url = resource_url

    if not is_session_active(state_session.get('expires_at')):
        redirect_view = reverse('pod_session:resource_delete') + f'?url={resource_url}'
        refresh_token_view = reverse('connector:session-refresh-token')
        refresh_token_query = f'{refresh_token_view}?redirect_uri={redirect_view}'
        return redirect(refresh_token_query)

    headers = get_headers(access_token=state_session['access_token'],
                          DPoP_key=state_session['DPoP_key'],
                          url=resource_url,
                          method='DELETE')

    api = SolidAPI(headers=headers)
    resp = api.delete(url=resource_url)  #, headers=headers)

    if resp.status_code == 401:
        messages.warning(request,
                         f"Got 401 trying to access {resource_url} . Please, log in to your pod provider before looking up for a resource")
    elif resp.status_code == 500:
        messages.error(request,
                         f"Error: 500 trying to delete {resource_url} .")
    elif resp.status_code != 205 and resp.status_code != 200:  # reset content
        messages.warning(request, f"Error: {resp.status_code} {resp.text}")
    else:  # resp.status_code == 205
        if redirect_url[-1] == '/':
            redirect_url = redirect_url[:-1]
        redirect_url = redirect_url[:redirect_url.rfind('/')] + '/'
        messages.success(request, f"{resource_url}  deleted.")
    view_url = reverse('pod_session:resource_view')
    return HttpResponseRedirect(f'{view_url}?url={redirect_url}')
