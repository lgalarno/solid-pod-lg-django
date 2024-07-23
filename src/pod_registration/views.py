from django.conf import settings
from django.contrib import messages
from django.shortcuts import render, reverse, get_object_or_404, HttpResponseRedirect, HttpResponse, redirect
from django.views.decorators.http import require_http_methods

from pathlib import Path

from connector.solid_api import SolidAPI
from connector.oidc import get_headers
from connector.utillities.minis import get_parent_url

from .models import SolidPod, StateSession

# Create your views here.
_MEDIA_ROOT = Path(settings.MEDIA_ROOT)
_MEDIA = Path(settings.MEDIA_URL)

def dashboard(request):
    # sessions = StateSession.objects.filter(user=request.user)  # contains WebID
    sessions = StateSession.objects.with_webid(user=request.user)
    pods = SolidPod.objects.filter(user=request.user)
    context = {
        'title': 'dashboard',
        'sessions': sessions,  # contains WebID
        'pods': pods,
        #'oidcps': oidcps
    }
    return render(request, "pod_registration/dashboard.html", context)


def view_resource(request, pk):
    """
    :param request:
    :param pk: SolidPod pk
    :return:
    """
    resource_content = None
    state_session_pk = request.session['session_pk']
    state_session = get_object_or_404(StateSession, pk=state_session_pk)
    pod = get_object_or_404(SolidPod, pk=pk)
    context = {
        'title': 'view_resource',
        'state_session_pk': pk,
        'pod': pod.url
    }
    if request.method == "POST":
        resource_url = pod.url
    elif request.method == "GET":
        resource_url = request.GET.get("url")

    if resource_url:
        # request = refresh_token(request=request, state_session=state_session)

        if not state_session.is_active:
            redirect_view = reverse('pod_registration:view_resource', kwargs={'pk': pk}) + f'?url={resource_url}'
            refresh_token_query = state_session.refresh_token_query(redirect_view=redirect_view)
            return redirect(refresh_token_query)

        headers = get_headers(access_token=state_session.access_token,
                              DPoP_key=state_session.DPoP_key,
                              url=resource_url,
                              method='GET')
        api = SolidAPI(headers=headers)  # , pod=pod.url)
        resp = api.get(url=resource_url)
        # resp = requests.get(url=lookup_url, headers=headers)
        #print(resource_content)
        if resp.status_code == 401:
            messages.warning(request,
                             f"Got 401 trying to access {resource_url} . Please, log in to your pod provider before looking up for a resource")
        elif resp.status_code == 403:
            messages.warning(request,
                             f"403 Forbidden. Insufficient rights to a resource to access {resource_url}")
        elif resp.status_code != 200:
            messages.error(request, f"Error: {resp.status_code} {resp.text}")
        else:  # resp.status_code == 200
            pod.viewed()  # update last viewed
            resource_content = resp.text
            content_type = resp.headers.get('Content-Type')
            if 'text/turtle' in content_type:
                folder_data = api.read_folder_offline(url=resource_url, ttl=resource_content, pod=pod.url)
                if folder_data:  # if folder_data is a container
                    for f in folder_data.folders:
                        f.view_url = reverse('pod_registration:view_resource',
                                             kwargs={'pk': pk}) + f'?url={f.url}'
                        f.del_url = reverse('pod_registration:delete_resource',
                                            kwargs={'pk': pk}) + f'?url={f.url}'
                    for f in folder_data.files:
                        f.view_url = reverse('pod_registration:view_resource',
                                             kwargs={'pk': pk}) + f'?url={f.url}'
                        f.del_url = reverse('pod_registration:delete_resource',
                                            kwargs={'pk': pk}) + f'?url={f.url}'
                        f.download_url = reverse('pod_registration:download_resource',
                                                 kwargs={'pk': pk}) + f'?url={f.url}'
                        f.preview_url = reverse('pod_registration:preview_resource',
                                                kwargs={'pk': pk}) + f'?url={f.url}'
                    context['folder_data'] = folder_data

            else:  # content_type.startswith('application'):
                fn = Path(resource_url).name
                response = HttpResponse(
                    resp.content,
                    content_type=resp.headers.get('Content-Type'),
                    headers={f'Content-Disposition': f"attachment; filename = {fn}"},
                )
                return response
        context['resource_content'] = resource_content  # ttl
        context['lookup_url'] = resource_url
    return render(request,
                  'pod_registration/view_resource.html',
                  context=context
                  )


#TODO create container and resources
@require_http_methods(["POST"])
def create_container(request, pk):
    state_session_pk = request.session['session_pk']
    state_session = get_object_or_404(StateSession, pk=state_session_pk)
    resource_url = request.POST.get("lookup_url")


@require_http_methods(["POST"])
def create_resource(request, pk):
    state_session_pk = request.session['session_pk']
    state_session = get_object_or_404(StateSession, pk=state_session_pk)
    resource_url = request.POST.get("lookup_url")


@require_http_methods(["POST"])
def upload_resource(request, pk):
    """
    :param request:
    :param pk: SolidPod pk
    :return:
    """
    state_session_pk = request.session['session_pk']
    state_session = get_object_or_404(StateSession, pk=state_session_pk)
    resource_url = request.POST.get("lookup_url")

    if not resource_url[-1] == '/':
        messages.warning(request,
                         f"You can't upload a file here. {resource_url} is not a container")
        # raise Exception(f'Cannot use putFile to create a folder : {lookup_url}')
    else:
        fn = request.FILES['to_pod'].name
        data = request.FILES['to_pod'].read()
        new_resource_url = resource_url + fn
        if not state_session.is_active:
            refresh_token_query = state_session.refresh_token_query(redirect_view=reverse('pod_registration:view_resource',
                                                                                          kwargs={'pk': pk})
                                                                    )
            messages.warning(request,
                             f"Please, try again.")
            return redirect(refresh_token_query)
        headers = get_headers(access_token=state_session.access_token,
                              DPoP_key=state_session.DPoP_key,
                              url=resource_url,
                              method='POST')

        api = SolidAPI(headers=headers)
        resp = api.post_file(url=new_resource_url, content=data, content_type=request.FILES['to_pod'].content_type)  #, headers=headers)
        # resp = requests.post(new_resource_url, headers=headers, data=data)  # files=files)
        if resp.status_code == 401:
            messages.warning(request,
                             f"Got 401 trying to post {new_resource_url} . You are not authorized to proceed.")
        elif resp.status_code != 201 and resp.status_code != 200:
            messages.warning(request, f"Error: {resp.status_code} {resp.text}")
        else:  # resp.status_code == 201:
            messages.success(request, f"{fn} uploaded to {resource_url}")
    read_url = reverse('pod_registration:view_resource', kwargs={'pk': pk})
    return HttpResponseRedirect(f'{read_url}?url={resource_url}')


def update_resource(request, pk):
    pass


def delete_resource(request, pk):
    state_session_pk = request.session['session_pk']
    state_session = get_object_or_404(StateSession, pk=state_session_pk)
    resource_url = request.GET.get("url")
    redirect_url = resource_url
    # request = refresh_token(request=request, state_session=state_session)
    if not state_session.is_active:
        redirect_view = reverse('pod_registration:delete_resource', kwargs={'pk': pk}) + f'?url={resource_url}'
        refresh_token_query = state_session.refresh_token_query(redirect_view=redirect_view)
        return redirect(refresh_token_query)

    headers = get_headers(access_token=state_session.access_token,
                          DPoP_key=state_session.DPoP_key,
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
    read_url = reverse('pod_registration:view_resource', kwargs={'pk': pk})
    return HttpResponseRedirect(f'{read_url}?url={redirect_url}')


def download_resource(request, pk):
    state_session_pk = request.session['session_pk']
    state_session = get_object_or_404(StateSession, pk=state_session_pk)
    resource_url = request.GET.get("url")
    if not state_session.is_active:
        redirect_view = reverse('pod_registration:download_resource', kwargs={'pk': pk}) + f'?url={resource_url}'
        refresh_token_query = state_session.refresh_token_query(redirect_view=redirect_view)
        return redirect(refresh_token_query)
    headers = get_headers(access_token=state_session.access_token,
                          DPoP_key=state_session.DPoP_key,
                          url=resource_url,
                          method='GET')
    api = SolidAPI(headers=headers)
    resp = api.get(url=resource_url)
    if resp.status_code == 401:
        messages.warning(request,
                         f"Got 401 trying to access {resource_url} . Please, log in to your pod provider before looking up for a resource")
    elif resp.status_code == 403:
        messages.warning(request,
                         f"403 Forbidden. Insufficient rights to a resource to access {resource_url}")
    elif resp.status_code == 404:
        messages.error(request,f"404 File not found.")
    elif resp.status_code != 200:
        messages.error(request, f"Error: {resp.status_code} {resp.text}")
    else:  # resp.status_code == 200
        fn = Path(resource_url).name
        response = HttpResponse(
            resp.content,
            content_type=resp.headers.get('Content-Type'),
            headers={f'Content-Disposition': f"attachment; filename = {fn}"},
        )
        return response
    parent_url = get_parent_url(resource_url)
    read_url = reverse('pod_registration:view_resource', kwargs={'pk': pk})
    return HttpResponseRedirect(f'{read_url}?url={parent_url}')


def preview_resource(request, pk):
    state_session_pk = request.session['session_pk']
    state_session = get_object_or_404(StateSession, pk=state_session_pk)
    resource_url = request.GET.get("url")
    if not state_session.is_active:
        redirect_view = reverse('pod_registration:download_resource', kwargs={'pk': pk}) + f'?url={resource_url}'
        refresh_token_query = state_session.refresh_token_query(redirect_view=redirect_view)
        return redirect(refresh_token_query)
    headers = get_headers(access_token=state_session.access_token,
                          DPoP_key=state_session.DPoP_key,
                          url=resource_url,
                          method='GET')
    api = SolidAPI(headers=headers)
    resp = api.get(url=resource_url)
    if resp.status_code == 401:
        messages.warning(request,
                         f"Got 401 trying to access {resource_url} . Please, log in to your pod provider before looking up for a resource")
    elif resp.status_code == 403:
        messages.warning(request,
                         f"403 Forbidden. Insufficient rights to a resource to access {resource_url}")
    elif resp.status_code == 404:
        messages.error(request, f"404 File not found.")
    elif resp.status_code != 200:
        messages.error(request, f"Error: {resp.status_code} {resp.text}")
    else:  # resp.status_code == 200
        fn = Path(resource_url).name
        resp_headers = resp.headers
        content_type = resp_headers.get('content-type')
        file = resp.content
        if 'text/turtle' in content_type:
            context = {
                'file': file,
                'filename': fn,
                'content_type': content_type
            }
            return render(request, 'pod_registration/partials/ttl_file.html', context)
        if 'text' in content_type:
            try:
                file = file.decode('utf-8')
                context = {
                    'file': file,
                    'filename': fn,
                    'content_type': content_type
                }
                return render(request, 'pod_registration/partials/text_file.html', context)
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
            return render(request, 'pod_registration/partials/image_file.html', context)
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
            return render(request, 'pod_registration/partials/audio_file.html', context)
        else:
            messages.warning(request, f'Unsupported file type: {content_type}')
    parent_url = get_parent_url(resource_url)
    read_url = reverse('pod_registration:view_resource', kwargs={'pk': pk})
    response = HttpResponse()
    response["HX-Redirect"] = f'{read_url}?url={parent_url}'
    return response

