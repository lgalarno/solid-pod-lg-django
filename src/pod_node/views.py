from django.contrib import messages
from django.http import Http404
from django.shortcuts import render, HttpResponse, redirect, HttpResponseRedirect, reverse

from connector.solid_api import SolidAPI

import httpx
import requests
# Create your views here.


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
    context = {
        'title': 'pod-node',
    }
    return render(request, 'pod_node/pod_node.html', context)


def login(request):
    url = 'http://localhost:3030/solid-pod-lg/login'
    return HttpResponseRedirect(url)


def login_callback(request):
    print(request.GET)
    sessionId = request.GET.get('sessionId')
    isLoggedIn = request.GET.get('isLoggedIn') == 'true'
    webId = request.GET.get('webId')
    request.session['node_sessionId'] = sessionId
    request.session['node_webId'] = webId
    request.session['node_isLoggedIn'] = isLoggedIn
    context = {
        'title': 'login-callback'
    }
    return render(request, 'pod_node/pod_node.html', context)


def view_resource(request):
    print('view_resource')
    sessionId = request.session.get('node_sessionId')
    # webId = request.session.get('node_webId')

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

    # resource_url = 'https://solid.insightdatalg.ca/lgalarno/profile/'
    fetch_url = 'http://localhost:3030/solid-pod-lg/fetch'
    fetch_url = fetch_url + f'/?sessionId={sessionId}&resource={resource_url}'
    print(fetch_url)
    try:
        r = httpx.get(fetch_url)
    except:
        messages.error(request,
                         'No response from solid-pod-lg API')
        return render(request, 'pod_node/pod_node.html', context)

    json_data = r.json()
    if r.status_code == 200:
        resource_content = json_data.get('resource_content')
        # print(resource_content)
        api = SolidAPI(headers=None)
        folder_data = api.read_folder_offline(url=resource_url, ttl=resource_content, pod=None)
        if folder_data:  # if folder_data is a container
            for f in folder_data.folders:
                f.view_url = reverse('pod_node:view_resource') + f'?url={f.url}'
                f.del_url = reverse('pod_node:view_resource') + f'?url={f.url}'
            for f in folder_data.files:
                f.view_url = reverse('pod_node:view_resource') + f'?url={f.url}'
                f.del_url = reverse('pod_node:view_resource') + f'?url={f.url}'
            context['folder_data'] = folder_data

        context['resource_content'] = resource_content

    elif r.status_code == 500:
        messages.error(request,
                       json_data.get('error'))

    return render(request, 'pod_node/view_resource.html', context)


def logout(request):
    print('logout')
    sessionId = request.session.get('node_sessionId')
    logout_url = 'http://localhost:3030/solid-pod-lg/logout'
    logout_url = logout_url + f'/?sessionId={sessionId}'
    print(logout_url)
    #try:
    r = httpx.get(logout_url)
    if r.status_code == 500:
        json_data = r.json()
        messages.error(request,
                       json_data.get('error'))
    request.session['node_sessionId'] = None
    request.session['node_webId'] = None
    request.session['node_isLoggedIn'] = False
    # except:
    #     messages.error(request,
    #                    'No response from solid-pod-lg API')
    return redirect('pod_node:pod_node')
