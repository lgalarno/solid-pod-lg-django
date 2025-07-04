from django.conf import settings
from django.contrib import messages
from django.http import Http404, JsonResponse
from django.shortcuts import render, HttpResponse, redirect, HttpResponseRedirect, reverse
from django.utils.http import urlencode

from pathlib import Path

import httpx
import requests

from .backend import get_folder_content, reset_session, error_check
from connector.utillities.minis import get_parent_url


# Create your views here.

_API_CALLBACK_URI = settings.API_CALLBACK_URI
_NODE_API_BROWSER_URL = settings.NODE_API_BROWSER_URL
_NODE_API_URL = settings.NODE_API_URL
_MEDIA_ROOT = Path(settings.MEDIA_ROOT)
_MEDIA = Path(settings.MEDIA_URL)


def test(request):
    node_api_url = f'{_NODE_API_URL}admin/alive/'
    print(node_api_url)
    resp = httpx.get(node_api_url)  # check id node api is alive
    print(resp.status_code)
    json_data = resp.json()
    print(json_data)
    return JsonResponse(json_data, safe=False)
    # try:
    #     resp = httpx.post(node_api_url, json=payload)  # refresh session info and check id node api is alive
    #     json_data = resp.json()
    # except:
    #     messages.error(request,
    #                    'No response from solid-pod-lg API')
    # sessionId = request.session.get('node_sessionId')
    # webId = request.session.get('node_webId')
    # context = {
    #     'title': 'test-nodeAPI',
    #     'webId': webId
    # }
    # resource_url = 'https://solid.insightdatalg.ca/lgalarno/'
    # payload = {
    #     'sessionId': sessionId,
    #     'resourceURL': resource_url
    # }
    # #
    # node_api_url = f'{_NODE_API_URL}resources/getpodurl/'
    # print(node_api_url)
    # r = httpx.post(node_api_url, json=payload)
    # json_data = r.json()
    # print(json_data)
    # folder_data = get_folder_content(data=json_data.get('folder_content'), url=resource_url)
    # if folder_data:  # if folder_data is a container
    #     print('folders')
    #     for f in folder_data.folders:
    #         print(f.name)
    #     print('files')
    #     for f in folder_data.files:  # preview, download and delete liks
    #         print(f.name)
    #     context['folder_data'] = folder_data
    # if r.status_code == 200:
    #     resource_content = json_data.get('resource_content')
    #     context['resource_content'] = resource_content
    #
    # elif r.status_code == 500:
    #     messages.error(request,
    #                    json_data.get('error'))
    #
    # try:
    #     r = httpx.post(node_api_url, json=payload)
    #     json_data = r.json()
    #     print(json_data)
    #     print('folders')
    #     for f in json_data.folders:
    #         print(f.url)
    #     for f in json_data.files:
    #         print(f.url)
    #         print(f.size)
    #
    #     if r.status_code == 200:
    #         resource_content = json_data.get('resource_content')
    #         context['resource_content'] = resource_content
    #
    #     elif r.status_code == 500:
    #         messages.error(request,
    #                        json_data.get('error'))
    # except:
    #     messages.error(request,
    #                      'No response from solid-pod-lg API')
    # return render(request, 'pod_node/pod_node.html', context)


# def alive(request):
#     context = {
#     }
#     payload = {
#         'sessionId': request.session.get('node_sessionId'),
#         'resourceURL': resource_url
#     }
#     is_dataset_url = f'{_NODE_API_URL}resources/dataset/'
#     resp = httpx.post(is_dataset_url, json=payload)


def sessions(request):
    print('sessions')
    print('----------------------------------------------------')
    node_api_url = f'{_NODE_API_URL}admin/sessions/'
    print(node_api_url)
    # url = 'http://localhost:3030/solid-pod-lg/sessions'
    # node_api_url = "http://solid_node_api:3030/api/admin/sessions"
    r = httpx.get(node_api_url)
    # r = httpx.get(url)
    print(r.status_code)
    return HttpResponse(f"Session: {r.text}")


def pod_node(request):
    json_data = {
        "sessionId": request.session.get('node_sessionId'),
        "webId": request.session.get('node_webId'),
        "isLoggedIn": request.session.get('node_isLoggedIn'),
    }
    if json_data.get("isLoggedIn"):
        payload = {'sessionId': json_data.get("sessionId")}
        node_api_url = f'{_NODE_API_URL}auth/session'
        try:
            resp = httpx.post(node_api_url, json=payload)  # refresh session info and check id node api is alive
            json_data = resp.json()
        except:
            messages.error(request,
                           'No response from solid-pod-lg API')
    else:
        json_data = {}
    reset_session(request, json_data)
    context = {
        'title': 'pod-node',
    }
    return render(request, 'pod_node/pod_node.html', context)


def login(request):
    print('login node.js')
    # issuer_url = 'https://login.inrupt.com/'
    issuer_url = 'https://solid.insightdatalg.ca/'
    context = {}
    if request.method == 'POST':
        issuer_url = request.POST.get('issuer_url').strip()
        context['issuer_url'] = issuer_url
        if issuer_url[-1] != '/':
            issuer_url = issuer_url + '/'
    payload = {
        'issuer_url': issuer_url,
        'callback_uri': _API_CALLBACK_URI,
    }
    login_url = f'{_NODE_API_BROWSER_URL}auth/login/?' + urlencode(payload)
    return HttpResponseRedirect(login_url)


def login_callback(request):
    session_info = {
        'sessionId': request.GET.get('sessionId'),
        'isLoggedIn': request.GET.get('isLoggedIn') == 'true',
        'webId': request.GET.get('webId')
    }
    reset_session(request, session_info)
    context = {
        'title': 'login-callback'
    }
    return render(request, 'pod_node/pod_node.html', context)


def logout(request):
    payload = {
        'sessionId': request.session.get('node_sessionId'),
    }
    logout_url = f'{_NODE_API_URL}auth/logout/'
    try:
        resp = httpx.post(logout_url, json=payload)
        json_data = resp.json()
        status_code = json_data.get('status')
        mess = json_data.get('text')
        if status_code == 500:
            messages.error(request, f'Error {status_code}: {mess}')
        else:
            messages.success(request, mess)
        reset_session(request, session_info={})
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
    is_dataset_url = f'{_NODE_API_URL}resources/dataset/'
    resp = httpx.post(is_dataset_url, json=payload)
    # try:
    #     resp = httpx.post(is_dataset_url, json=payload)
    # except:
    #     messages.error(request,
    #                      'No response from solid-pod-lg API')
    #     return redirect('pod_node:pod_node')

    json_data = resp.json()
    error = error_check(request, json_data=json_data)
    if not error:
        if json_data.get('dataset'):
            ttl = json_data.get('ttl')
            context['resource_content'] = ttl
            if json_data.get('container'):
                folder_url = f'{_NODE_API_URL}resources/folder/'
                try:
                    payload = {
                        'sessionId': request.session.get('node_sessionId'),
                        'resourceURL': resource_url
                    }
                    resp = httpx.post(folder_url, json=payload)
                except:
                    messages.error(request,
                                     'No response from solid-pod-lg API')
                    return redirect('pod_node:pod_node')
                json_data = resp.json()
                error = error_check(request, json_data=json_data)
                if not error:
                    folder_content = json_data.get('content')
                    if folder_content:
                        folder_data = get_folder_content(data=folder_content, url=resource_url)
                        context['folder_data'] = folder_data
        else:
            messages.warning(request, 'Please, select a valid Solid dataset')
            return redirect('pod_node:pod_node')
    return render(request, 'pod_node/view_resource.html', context)


def preview_resource(request):
    resource_url = request.GET.get("url").strip()
    payload = {
        'sessionId': request.session.get('node_sessionId'),
        'resourceURL': resource_url
    }
    download_url = f'{_NODE_API_URL}resources/download/?' + urlencode(payload)
    try:
        resp = httpx.get(download_url)
    except:
        messages.error(request,
                       'No response from solid-pod-lg API')
        response = HttpResponse()
        response["HX-Redirect"] = reverse("pod_node:pod_node")
        return response
    if resp.status_code == 200:
        fn = Path(resource_url).name
        resp_headers = resp.headers
        content_type = resp_headers.get('content-type')
        file = resp.content
        if 'text/turtle' in content_type:
            context = {
                'file': file.decode('utf-8'),
                'filename': fn,
                'content_type': content_type
            }
            return render(request, 'pod_node/partials/ttl_file.html', context)
        if 'text' in content_type:
            try:
                file = file.decode('utf-8')
                context = {
                    'file': file,
                    'filename': fn,
                    'content_type': content_type
                }
                return render(request, 'pod_node/partials/text_file.html', context)
            except:
                messages.warning(request, f'Unsupported file type: {content_type}')

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
    else:
        json_data = resp.json()
        error = error_check(request, json_data=json_data)
    response = HttpResponse()
    parent_url = get_parent_url(resource_url)
    response["HX-Redirect"] = f'{reverse("pod_node:view_resource")}?url={parent_url}'
    return response


def download_resource(request):
    resource_url = request.GET.get("url").strip()
    payload = {
        'sessionId': request.session.get('node_sessionId'),
        'resourceURL': resource_url
    }
    # use _NODE_API_BROWSER_URL because response
    download_url = f'{_NODE_API_BROWSER_URL}resources/download/?' + urlencode(payload)
    return HttpResponseRedirect(download_url)


def delete_resource(request):
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
        resp = httpx.post(delete_url, json=payload)
    except:
        messages.error(request,
                         'No response from solid-pod-lg API')
        return render(request, 'pod_node/pod_node.html', context)
    json_data = resp.json()
    error = error_check(request, json_data=json_data)
    mess = json_data.get('text')
    if not error:
        messages.success(request, mess)
    return HttpResponseRedirect(reverse('pod_node:view_resource') + '?' + urlencode({'url': parent_url,}))


def create_resource(request):
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
    error = error_check(request, json_data=json_data)
    mess = json_data.get('text')
    if not error:
        messages.success(request, mess)
    return HttpResponseRedirect(reverse('pod_node:view_resource') + '?' + urlencode({'url': source_url,}))
