from django.shortcuts import render, get_object_or_404, HttpResponse

from pod_registration.forms import OpenIDproviderForm, SolidPodForm
from pod_registration.models import SolidPod, OpenIDprovider, StateSession


def issuer_list(request):
    context = {
        'oidcps': OpenIDprovider.objects.all(),
    }
    return render(request, 'pod_registration/partials/oidcps-list.html', context)


def pod_list(request):
    context = {
        'pods': SolidPod.objects.filter(user=request.user),
    }
    return render(request, 'pod_registration/partials/pods-list.html', context)


def create_issuer(request):
    form = OpenIDproviderForm(request.POST or None)
    if request.method == "POST":
        if form.is_valid():
            form.save()
            return HttpResponse(status=204, headers={'HX-Trigger': 'issuerListChanged'})
            # form = OpenIDproviderForm()
    if request.method == "GET":
        provider_form = request.session.get('provider_form')
        if provider_form:
            request.session['provider_form'] = False
            form = None
        else:
            request.session['provider_form'] = True
    sessions = StateSession.objects.with_webid(user=request.user)  # contains WebID
    oidcps = OpenIDprovider.objects.all()
    context = {
        "title": "create-webid",
        'form_provider': form,
        'sessions': sessions,  # contains WebID
        'oidcps': oidcps,
    }
    return render(request, 'pod_registration/partials/issuer-form.html', context)


def delete_webid(request, pk):
    s = get_object_or_404(StateSession, id=pk)
    s.delete()
    sessions = StateSession.objects.with_webid(user=request.user)
    context = {
        'sessions': sessions,
        'form': None,
    }
    return render(request, 'pod_registration/partials/webid-list.html', context)


def create_pod(request):
    form = SolidPodForm(request.POST or None)
    if request.method == "POST":
        if form.is_valid():
            instance = form.save(commit=False)
            instance.user = request.user
            instance.save()
            return HttpResponse(status=204, headers={'HX-Trigger': 'podListChanged'})

    if request.method == "GET":
        pod_form = request.session.get('pod_form')
        if pod_form:
            request.session['pod_form'] = False
            form = None
        else:
            request.session['pod_form'] = True
    pods = SolidPod.objects.filter(user=request.user)
    context = {
        'pod_registration': pods,
        'form_pod': form,
    }
    return render(request, 'pod_registration/partials/pod-form.html', context)


def delete_pod(request, pk):
    p = get_object_or_404(SolidPod, id=pk)
    p.delete()
    pods = SolidPod.objects.filter(user=request.user)
    context = {
        'pod_registration': pods,
        'form': None,
    }
    return render(request, 'pod_registration/partials/pods-list.html', context)
    # return render(request, 'pod_registration/partials/pod-form.html', context)

#####################################################
# Create resources in pods forms requests
#####################################################


def upload_file_(request):
    form = OpenIDproviderForm(request.POST or None)
    if request.method == "POST":
        if form.is_valid():
            form.save()
            return HttpResponse(status=204, headers={'HX-Trigger': 'issuerListChanged'})
            # form = OpenIDproviderForm()
    if request.method == "GET":
        provider_form = request.session.get('provider_form')
        if provider_form:
            request.session['provider_form'] = False
            form = None
        else:
            request.session['provider_form'] = True
    sessions = StateSession.objects.with_webid(user=request.user)  # contains WebID
    oidcps = OpenIDprovider.objects.all()
    context = {
        "title": "create-webid",
        'form_provider': form,
        'sessions': sessions,  # contains WebID
        'oidcps': oidcps,
    }
    return render(request, 'pod_registration/partials/issuer-form.html', context)
