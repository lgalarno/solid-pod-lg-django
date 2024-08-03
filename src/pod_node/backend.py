from django.contrib import messages
from django.shortcuts import reverse

from hurry.filesize import size

import urllib.parse

from connector.utillities.minis import get_item_name
import urllib.parse


class Item:
    def __init__(self):
        self.root = None
        self.url = None
        self.name = None
        self.size = None
        self.view_url = None
        self.del_url = None
        self.preview_url = None
        self.download_url = None
        self.itemType = None  # "Container" | "Resource"


class FolderData:
    def __init__(self):
        self.url = None
        self.name = None
        self.parent = None
        self.view_parent_url = None
        self.type = 'folder'


def remove_slashes_at_end(url) -> str:
    if url[-1] == '/':
        url = url[:-1]
    return url


def get_item_name(url) -> str:
    temp = remove_slashes_at_end(url)
    i = temp.rindex('/')
    return urllib.parse.unquote(url[i + 1:])


def get_folder_content(data=None, url=None):

    folders, files = [], []
    for d in data:
        is_container = d.get('container', False)
        item = Item()
        item.url = d.get('url', None)
        item.name = get_item_name(item.url)
        if d.get('size', None):
            item.size = size(d.get('size', None))
        item.view_url = reverse('pod_node:view_resource') + f'?url={item.url}'
        item.del_url = reverse('pod_node:delete_resource') + f'?url={item.url}'
        if not is_container:
            item.preview_url = reverse('pod_node:preview_resource') + f'?url={item.url}'
            item.download_url = reverse('pod_node:download_resource') + f'?url={item.url}'
        item.itemType = 'Container' if is_container else 'Resource'
        cat = folders if is_container else files
        cat.append(item)
    ret = FolderData()
    ret.url = url
    ret.name = get_item_name(url)
    ret.folders = folders
    ret.files = files
    return ret


def reset_session(request, session_info=None):
    request.session['node_sessionId'] = session_info.get('sessionId')
    request.session['node_webId'] = session_info.get('webId')
    request.session['node_isLoggedIn'] = session_info.get('isLoggedIn')
    return True


def error_check(request, json_data):
    status_code = json_data.get('status')
    resource_url = json_data.get('resourceUrl')
    mess = json_data.get('text')
    error = True
    if status_code >= 200 and status_code < 300:
        error = False
    elif status_code == 401:
        messages.error(request, f"Error: {status_code} trying to access {resource_url} . Please, log in to your pod provider before looking up for a resource")
    elif status_code == 403:
        messages.error(request, f"Error: {status_code}  Insufficient rights to a resource to access {resource_url}")
    elif status_code == 500 and mess == 'Error 500: No session found.':
        reset_session(request, session_info={})
        messages.error(request, mess)
    else:
        messages.error(request, mess)
    return error
