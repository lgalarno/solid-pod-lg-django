from django.utils.http import quote
from enum import Enum
from typing import List

import urllib.parse

import base64
import os
import re


class LINK(Enum):
    CONTAINER = '<http://www.w3.org/ns/ldp#BasicContainer>; rel="type"'
    RESOURCE = '<http://www.w3.org/ns/ldp#Resource>; rel="type"'


def append_slashes_at_end(url) -> str:
    if url[-1] != '/':
        url += '/'
    return url


def remove_slashes_at_end(url) -> str:
    if url[-1] == '/':
        url = url[:-1]
    return url


def get_root_url(url: str) -> str:
    slash_count = 0
    for i in range(len(url)):
        if url[i] == '/':
            slash_count += 1
        if slash_count == 3:
            break

    if slash_count == 3:
        return url[:i + 1]
    else:
        return append_slashes_at_end(url)


def get_parent_url(url) -> str:
    #print(url)
    url = remove_slashes_at_end(url)
    if url.count('/') == 2:  # is base url, no parent url, return itself
        return append_slashes_at_end(url)

    i = url.rindex('/')
    return url[:i + 1]


def get_item_name(url) -> str:
    # url = remove_slashes_at_end(url)

    # if url.count('/') == 3:  # is base url, no item name
    #     return ''
    temp = remove_slashes_at_end(url)
    i = temp.rindex('/')
    return urllib.parse.unquote(url[i + 1:])


def are_folders(urls: List) -> bool:
    pass


def are_files(urls: List) -> bool:
    pass
