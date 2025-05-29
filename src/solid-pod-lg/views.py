from django.conf import settings
from django.contrib import messages
from django.shortcuts import render
import httpx

_NODE_API_URL = settings.NODE_API_URL


def home(request):
    node_api_url = f'{_NODE_API_URL}admin/alive/'
    try:
        resp = httpx.get(node_api_url)  # check id node api is alive
        if resp.status_code == 200:
            alive = True
        else:
            messages.warning(request, f"*** Connection to the node.js api was denied ***")
            alive = False
    except:
        messages.warning(request, f"*** The node.js api is down ***")
        alive = False

    context = {
        'title': 'index',
        'node_api_alive': alive,
    }
    return render(request, "index.html", context)
