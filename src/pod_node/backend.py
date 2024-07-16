from hurry.filesize import size


class Item:
    def __init__(self):
        self.url = None
        self.name = None
        self.size = None
        self.view_url = None
        self.del_url = None
        self.parent = None
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
    url = remove_slashes_at_end(url)

    if url.count('/') == 2:  # is base url, no item name
        return ''

    i = url.rindex('/')
    return url[i + 1:]


def get_item_size(s):
    return size(int(s))


def parse_folder_old(folder_content) -> dict:
    # folder_data = {
    #     'file': {},
    #     'folder': {}
    # }
    folders, files = [], []
    for i in folder_content:
        if folder_content[i]['isContainer']:
            pass

    return {}


def parse_folder_content(folder_content, resource_url, pod_url):

    folders, files = [], []
    item = Item()  # create parent item
    item.name = '../'  # get_item_name(this) Parent url
    if resource_url == pod_url:
        item.url = this
        print('url == pod')
    else:
        item.url = get_parent_url(url)
        print('url != pod')
    print(item.url)
    item.itemType = 'Container' if is_container(this) else 'Resource'
    cat = folders if is_container(this) else files
    cat.append(item)

    # TODO solidcommunity root folder
    for obj in g.objects(this, LDP.contains):
        item_url = str(obj)
        item = Item()
        # item.parent = get_parent_url(item_url)
        # item.links = None
        item.name = get_item_name(item_url)
        # get size of the file
        item.size = get_item_size(item_url)
        print(item.size)
        item.url = item_url
        item.itemType = 'Container' if is_container(obj) else 'Resource'
        cat = folders if is_container(obj) else files
        cat.append(item)

    ret = FolderData()
    ret.url = url
    ret.name = get_item_name(url)
    # print('get folder parent', pod)
    # ret.parent = get_parent_url(url)
    # ret.links = None  #
    ret.folders = folders
    ret.files = files

    return ret
