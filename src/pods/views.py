from django.contrib import messages
from django.shortcuts import render, reverse, get_object_or_404, HttpResponseRedirect, HttpResponse, redirect
from django.views.decorators.http import require_http_methods

from pathlib import Path

from connector.solid_api import SolidAPI
from connector.views import refresh_token
from connector.oidc import get_headers

from .models import OpenIDprovider,  SolidPod, StateSession

# Create your views here.


# TODO login with web id with select
def dashboard(request):
    sessions = StateSession.objects.filter(user=request.user)  # contains WebID
    pods = SolidPod.objects.filter(user=request.user)
    # for s in sessions:
    #     print(s.webid)
    oidcps = OpenIDprovider.objects.all()
    context = {
        'title': 'dashboard',
        'sessions': sessions,  # contains WebID
        'pods': pods,
        'oidcps': oidcps
    }
    return render(request, "pods/dashboard.html", context)


@require_http_methods(["POST"])
def connect_webid(request):
    pk = request.POST.get('session_id')
    s = get_object_or_404(StateSession, pk=pk)
    request = refresh_token(request=request, state_session=s)
    return redirect('pods:dashboard')


def view_resource(request, pk):
    print("view_resource")
    state_session_pk = request.session['session_pk']
    state_session = get_object_or_404(StateSession, pk=state_session_pk)
    print(state_session)
    pod = get_object_or_404(SolidPod, pk=pk)
    context = {
        'title': 'view_resource',
        'state_session_pk': pk,
        'pod': pod.url
    }
    if request.method == "POST":
        print("crud read POST")
        lookup_url = pod.url
    elif request.method == "GET":
        print("crud read GET")
        lookup_url = request.GET.get("url")

    if lookup_url:
        print(lookup_url)
        request = refresh_token(request=request, state_session=state_session)
        headers = get_headers(access_token=state_session.access_token,
                              DPoP_key=state_session.DPoP_key,
                              lookup_url=lookup_url,
                              method='GET')
        api = SolidAPI(headers=headers)
        resp = api.get(url=lookup_url)
        # resp = requests.get(url=lookup_url, headers=headers)
        resource_content = resp.text
        #print(resource_content)
        if resp.status_code == 401:
            messages.warning(request,
                             f"Got 401 trying to access {lookup_url} . Please, log in to your pod provider before looking up for a resource")
        elif resp.status_code == 403:
            messages.warning(request,
                             f"403 Forbidden. Insufficient rights to a resource to access {lookup_url}")
        elif resp.status_code != 200:
            messages.warning(request, f"Error: {resp.status_code} {resp.text}")
        else:  # resp.status_code == 200
            content_type = resp.headers.get('Content-Type')
            if content_type == 'text/turtle':
                print( 'text/turtle')
                folder_data = api.read_folder_offline(url=lookup_url, ttl=resource_content)
                folder_data.view_parent_url = reverse('pods:view_resource', kwargs={'pk': pk}) + f'?url={folder_data.parent}'
                if folder_data:  # if folder_data is a container
                    for f in folder_data.folders:
                        f.view_url = reverse('pods:view_resource', kwargs={'pk': pk}) + f'?url={f.url}'
                        f.del_url = reverse('pods:delete_resource', kwargs={'pk': pk}) + f'?url={f.url}'
                    for f in folder_data.files:
                        f.view_url = reverse('pods:view_resource', kwargs={'pk': pk}) + f'?url={f.url}'
                        f.del_url = reverse('pods:delete_resource', kwargs={'pk': pk}) + f'?url={f.url}'
                    context['folder_data'] = folder_data

            else:  # content_type.startswith('application'):
                print('else')
                fn = Path(lookup_url).name
                response = HttpResponse(
                    resp.content,
                    content_type=resp.headers.get('Content-Type'),
                    headers={f'Content-Disposition': f"attachment; filename = {fn}"},
                )
                return response

        context['resource_content'] = resource_content
        context['lookup_url'] = lookup_url

    return render(request,
                  'pods/view_resource.html',
                  context=context
                  )


@require_http_methods(["POST"])
def create_resource(request, pk):
    print("create_resource")
    state_session_pk = request.session['session_pk']
    state_session = get_object_or_404(StateSession, pk=state_session_pk)
    lookup_url = request.POST.get("lookup_url")

    if not lookup_url[-1] == '/':
        messages.warning(request,
                         f"You can't upload a file here. {lookup_url} is not a container")
        # raise Exception(f'Cannot use putFile to create a folder : {lookup_url}')
    else:
        fn = request.FILES['to_pod'].name
        data = request.FILES['to_pod'].read()
        new_resource_url = lookup_url + fn
        headers = get_headers(access_token=state_session.access_token,
                              DPoP_key=state_session.DPoP_key,
                              lookup_url=lookup_url,
                              method='POST')
        request = refresh_token(request=request, state_session=state_session)
        api = SolidAPI(headers=headers)
        resp = api.post_file(url=new_resource_url, content=data, content_type=request.FILES['to_pod'].content_type)  #, headers=headers)
        # resp = requests.post(new_resource_url, headers=headers, data=data)  # files=files)
        if resp.status_code == 401:
            messages.warning(request,
                             f"Got 401 trying to post {new_resource_url} . You are not authorized to proceed.")
        elif resp.status_code != 201 and resp.status_code != 200:
            messages.warning(request, f"Error: {resp.status_code} {resp.text}")
        else:  # resp.status_code == 201:
            messages.success(request, f"{fn} uploaded to {lookup_url}")
    read_url = reverse('pods:view_resource', kwargs={'pk': pk})
    return HttpResponseRedirect(f'{read_url}?url={lookup_url}')


def update_resource(request, pk):
    pass


def delete_resource(request, pk):
    print("delete_resource")
    state_session_pk = request.session['session_pk']
    state_session = get_object_or_404(StateSession, pk=state_session_pk)
    lookup_url = request.GET.get("url")
    redirect_url = lookup_url
    if redirect_url[-1] == '/':
        redirect_url = redirect_url[:-1]
    redirect_url = redirect_url[:redirect_url.rfind('/')] + '/'

    headers = get_headers(access_token=state_session.access_token,
                          DPoP_key=state_session.DPoP_key,
                          lookup_url=lookup_url,
                          method='DELETE')
    request = refresh_token(request=request, state_session=state_session)
    api = SolidAPI(headers=headers)
    resp = api.delete(url=lookup_url)  #, headers=headers)

    if resp.status_code == 401:
        messages.warning(request,
                         f"Got 401 trying to access {lookup_url} . Please, log in to your pod provider before looking up for a resource")
    elif resp.status_code != 205 and resp.status_code != 200:  # reset content
        messages.warning(request, f"Error: {resp.status_code} {resp.text}")
    else:  # resp.status_code == 205
        messages.success(request, f"{lookup_url}  deleted.")
    read_url = reverse('pods:view_resource', kwargs={'pk': pk})
    return HttpResponseRedirect(f'{read_url}?url={redirect_url}')
