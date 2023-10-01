from django.shortcuts import render, get_object_or_404

from pods.forms import OpenIDproviderForm, SolidPodForm

from pods.models import SolidPod, OpenIDprovider, StateSession


def create_provider(request):
    form = OpenIDproviderForm(request.POST or None)
    if request.method == "POST":
        if form.is_valid():
            form.save()
            form = OpenIDproviderForm()
    if request.method == "GET":
        provider_form = request.session.get('provider_form')
        if provider_form:
            request.session['provider_form'] = False
            form = None
        else:
            request.session['provider_form'] = True
    sessions = StateSession.objects.filter(user=request.user)  # contains WebID
    oidcps = OpenIDprovider.objects.all()
    context = {
        "title": "create-webid",
        'form_provider': form,
        'sessions': sessions,  # contains WebID
        'oidcps': oidcps,
    }
    return render(request, 'pods/partials/provider-form.html', context)


def delete_webid(request, pk):
    s = get_object_or_404(StateSession, id=pk)
    s.delete()
    sessions = StateSession.objects.filter(user=request.user)
    context = {
        'sessions': sessions,
        'form': None,
    }
    return render(request, 'pods/partials/webid-list.html', context)


def create_pod(request):
    form = SolidPodForm(request.POST or None)
    if request.method == "POST":
        if form.is_valid():
            instance = form.save(commit=False)
            instance.user = request.user
            instance.save()
            form = SolidPodForm()

    if request.method == "GET":
        pod_form = request.session.get('pod_form')
        if pod_form:
            request.session['pod_form'] = False
            form = None
        else:
            request.session['pod_form'] = True
    pods = SolidPod.objects.filter(user=request.user)
    context = {
        'pods': pods,
        'form_pod': form,
    }
    return render(request, 'pods/partials/pod-form.html', context)


def delete_pod(request, pk):
    p = get_object_or_404(SolidPod, id=pk)
    p.delete()
    pods = SolidPod.objects.filter(user=request.user)
    context = {
        'pods': pods,
        'form': None,
    }
    return render(request, 'pods/partials/pod-form.html', context)
