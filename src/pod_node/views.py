from django.conf import settings
from django.core.files import File
from django.contrib import messages
from django.core.files.storage import FileSystemStorage
from django.http import Http404
from django.shortcuts import render, HttpResponse, redirect, HttpResponseRedirect, reverse
from django.utils.http import urlencode

from pathlib import Path

import httpx
import requests

from connector.solid_api import SolidAPI
from connector.utillities.minis import get_parent_url


# Create your views here.

_NODE_API_URL = settings.NODE_API_URL
_MEDIA_ROOT = Path(settings.MEDIA_ROOT)
_MEDIA = Path(settings.MEDIA_URL)


def _reset_session(request, session_info=None):
    request.session['node_sessionId'] = session_info.get('sessionId')
    request.session['node_webId'] = session_info.get('webId')
    request.session['node_isLoggedIn'] = session_info.get('isLoggedIn')
    return True


def test(request):
    sessionId = request.session.get('node_sessionId')
    webId = request.session.get('node_webId')
    context = {
        'title': 'test-nodeAPI',
        'webId': webId
    }
    resource = 'https://solid.insightdatalg.ca/lgalarno/'
    fetch_url = 'http://localhost:3030/solid-pod-lg/test'
    fetch_url = fetch_url + f'/?sessionId={sessionId}&resource={resource}'
    print(fetch_url)
    try:
        r = httpx.get(fetch_url)
        json_data = r.json()
        if r.status_code == 200:
            resource_content = json_data.get('resource_content')
            context['resource_content'] = resource_content
        elif r.status_code == 500:
            messages.error(request,
                           json_data.get('error'))
    except:
        messages.error(request,
                         'No response from solid-pod-lg API')
    return render(request, 'pod_node/pod_node.html', context)


def sessions(request):
    url = 'http://localhost:3030/solid-pod-lg/sessions'
    r = requests.get(url)
    # r = httpx.get(url)
    print(r.status_code)
    return HttpResponse("Hello World")


def pod_node(request):
    #TODO check with node server if logged in?
    sessionId = request.session.get('node_sessionId')
    if sessionId:
        payload = {'sessionId': sessionId}
        node_api_url = f'{_NODE_API_URL}auth/session'
        print(node_api_url)
        try:
            resp = requests.post(node_api_url, json=payload)
            json_data = resp.json()
        except:
            messages.error(request,
                           'No response from solid-pod-lg API')
    else:
        json_data = {}
    _reset_session(request, json_data)
    context = {
        'title': 'pod-node',
    }
    return render(request, 'pod_node/pod_node.html', context)


def login(request):
    print('login node.js')
    issuer_url = 'https://login.inrupt.com/'
    issuer_url = 'https://solid.insightdatalg.ca/'
    context = {}
    if request.method == 'POST':
        issuer_url = request.POST.get('issuer_url').strip()
        context['issuer_url'] = issuer_url
        if issuer_url[-1] != '/':
            issuer_url = issuer_url + '/'
    login_url = f'{_NODE_API_URL}auth/login/?issuer_url={issuer_url}'
    return HttpResponseRedirect(login_url)


def login_callback(request):
    print(request.GET)
    session_info = {
        'sessionId': request.GET.get('sessionId'),
        'isLoggedIn': request.GET.get('isLoggedIn') == 'true',
        'webId': request.GET.get('webId')
    }
    _reset_session(request, session_info)
    context = {
        'title': 'login-callback'
    }
    return render(request, 'pod_node/pod_node.html', context)


def logout(request):
    print('logout')
    payload = {
        'sessionId': request.session.get('node_sessionId'),
    }
    logout_url = f'{_NODE_API_URL}auth/logout/'
    try:
        resp = requests.post(logout_url, json=payload)
        json_data = resp.json()
        status_code = json_data.get('status')
        mess = json_data.get('text')
        if status_code == 500:
            messages.error(request, f'Error {status_code}: {mess}')
        else:
            messages.success(request, mess)
        _reset_session(request, session_info={})
    except:
        messages.error(request,
                       'No response from solid-pod-lg API')
    return redirect('pod_node:pod_node')


def view_resource(request):
    print('view_resource')

    if request.method == 'GET':
        resource_url = request.GET.get("url").strip()
    elif request.method == 'POST':
        resource_url = request.POST.get('resource_url').strip()
    else:
        raise Http404
    context = {
        'title': 'view-resource',
        'resource_url': resource_url
    }
    payload = {
        'sessionId': request.session.get('node_sessionId'),
        'resourceURL': resource_url
    }
    # resource_url = 'https://solid.insightdatalg.ca/lgalarno/profile/'
    # fetch_url = f'{_NODE_API_URL}fetch/?sessionId={sessionId}&resource={resource_url}'
    fetch_url = f'{_NODE_API_URL}resources/fetch/'
    try:
        resp = requests.post(fetch_url, json=payload)
    except:
        messages.error(request,
                         'No response from solid-pod-lg API')
        return render(request, 'pod_node/pod_node.html', context)
    json_data = resp.json()
    status_code = json_data.get('status')
    mess = json_data.get('text')
    if status_code == 200:
        resource_content = json_data.get('content')
        if resource_content:
            api = SolidAPI(headers=None)
            folder_data = api.read_folder_offline(url=resource_url, ttl=resource_content, pod=None)
            if folder_data:  # if folder_data is a container
                for f in folder_data.folders:
                    f.view_url = reverse('pod_node:view_resource') + f'?url={f.url}'
                    f.del_url = reverse('pod_node:delete_resource') + f'?url={f.url}'
                for f in folder_data.files:  # preview, download and delete liks
                    f.view_url = reverse('pod_node:view_resource') + f'?url={f.url}'
                    f.preview_url = reverse('pod_node:preview_resource') + f'?url={f.url}'
                    f.download_url = reverse('pod_node:download_resource') + f'?url={f.url}'
                    f.del_url = reverse('pod_node:delete_resource') + f'?url={f.url}'
                context['folder_data'] = folder_data

            context['resource_content'] = resource_content
        else:
            messages.error(request, f"Error: {status_code} {mess}")
    elif status_code == 401:
        messages.warning(request,
                         f"Error: {status_code} trying to access {resource_url} . Please, log in to your pod provider before looking up for a resource")
    elif status_code == 403:
        messages.warning(request,
                         f"Error: {status_code}  Insufficient rights to a resource to access {resource_url}")
    elif status_code == 500 and mess == 'Error 500: No session found.':
        _reset_session(request, session_info={})
        messages.error(request, mess)
    else:
        messages.error(request, mess)
    return render(request, 'pod_node/view_resource.html', context)


def preview_resource(request):
    print('preview_resource')
    resource_url = request.GET.get("url").strip()
    fn = Path(resource_url).name
    payload = {
        'sessionId': request.session.get('node_sessionId'),
        'resourceURL': resource_url
    }
    download_url = f'{_NODE_API_URL}resources/download/?' + urlencode(payload)
    resp = requests.get(download_url)
    if resp.status_code == 200:
        header = resp.headers
        content_type = header.get('content-type')
        file = resp.content
        if 'text/turtle' in content_type:
            context = {
                'file': file.decode('utf-8'),
                'filename': fn,
                'content_type': content_type
            }
            return render(request, 'pod_node/partials/ttl_file.html', context)
        if 'text' in content_type:
            context = {
                'file': file.decode('utf-8'),
                'filename': fn,
                'content_type': content_type
            }
            return render(request, 'pod_node/partials/text_file.html', context)
        elif 'image' in content_type:
            long_fn = _MEDIA_ROOT / fn
            if long_fn.exists():
                long_fn.unlink()
            with open(long_fn, 'wb') as f:
                f.write(file)
            context = {
                'file': _MEDIA / fn,
                'filename': fn,
                'content_type': content_type
            }
            return render(request, 'pod_node/partials/image_file.html', context)
        elif 'audio' in content_type:
            long_fn = _MEDIA_ROOT / fn
            if long_fn.exists():
                long_fn.unlink()
            with open(long_fn, 'wb') as f:
                f.write(file)
            context = {
                'file': _MEDIA / fn,
                'filename': fn,
                'content_type': content_type
            }
            return render(request, 'pod_node/partials/audio_file.html', context)
        else:
            messages.warning(request, f'Unsupported file type: {content_type}')

    elif resp.status_code == 500 and resp.text == 'Error 500: No session found.':
        _reset_session(request, session_info={})
        messages.error(request, resp.json().get('text'))
    else:
        messages.error(request, resp.json().get('text'))
    response = HttpResponse()
    parent_url = get_parent_url(resource_url)
    response["HX-Redirect"] = f'{reverse("pod_node:view_resource")}?url={parent_url}'
    return response


def download_resource(request):
    print('preview_resource')
    resource_url = request.GET.get("url").strip()
    payload = {
        'sessionId': request.session.get('node_sessionId'),
        'resourceURL': resource_url
    }
    download_url = f'{_NODE_API_URL}resources/download/?' + urlencode(payload)
    return HttpResponseRedirect(download_url)


def delete_resource(request):
    print('delete_resource')
    resource_url = request.GET.get("url").strip()
    parent_url = get_parent_url(resource_url)

    context = {
        'title': 'view-resource',
        'resource_url': resource_url
    }
    payload = {
        'sessionId': request.session.get('node_sessionId'),
        'resourceURL': resource_url
    }
    delete_url = f'{_NODE_API_URL}resources/delete/'

    try:
        resp = requests.post(delete_url, json=payload)
    except:
        messages.error(request,
                         'No response from solid-pod-lg API')
        return render(request, 'pod_node/pod_node.html', context)
    json_data = resp.json()
    status_code = json_data.get('status')
    mess = json_data.get('text')
    if status_code == 200 or status_code == 205:
        messages.success(request, mess)
    elif status_code == 500 and mess == 'Error 500: No session found.':
        _reset_session(request, session_info={})
        messages.error(request, mess)
    else:
        messages.error(request, mess)

    return HttpResponseRedirect(reverse('pod_node:view_resource') + '?' + urlencode({'url': parent_url,}))


def create_resource(request):
    print(request.POST)
    source_url = request.POST.get("source_url").strip()
    messages.warning(request,
                   'Not implemented yet')
    return HttpResponseRedirect(reverse('pod_node:view_resource') + '?' + urlencode({'url': source_url,}))


def create_container(request):
    source_url = request.POST.get("source_url").strip()
    messages.warning(request,
                   'Not implemented yet')
    return HttpResponseRedirect(reverse('pod_node:view_resource') + '?' + urlencode({'url': source_url,}))


def upload_resource(request):
    source_url = request.POST.get("source_url").strip()
    context = {
        'title': 'view-resource',
        'resource_url': source_url
    }
    payload = {
        'sessionId': request.session.get('node_sessionId'),
        'resourceURL': source_url
    }
    file = request.FILES["file"]
    files = [
        ('file', (file.name, file.read(), file.content_type)),
    ]
    upload_url = f'{_NODE_API_URL}resources/upload/'
    try:
        resp = requests.post(upload_url, data=payload, files=files)
    except:
        messages.error(request,
                         'No response from solid-pod-lg API')
        return render(request, 'pod_node/pod_node.html', context)
    json_data = resp.json()
    status_code = json_data.get('status')
    mess = json_data.get('text')
    if status_code == 200 or status_code == 201:
        messages.success(request, mess)
    elif status_code == 500 and mess == 'Error 500: No session found.':
        _reset_session(request, session_info={})
        messages.error(request, mess)
    else:
        messages.error(request, mess)
    return HttpResponseRedirect(reverse('pod_node:view_resource') + '?' + urlencode({'url': source_url,}))
