from hurry.filesize import size
from rdflib import Namespace, Graph, URIRef, RDF
from connector.utillities.minis import get_item_name, get_parent_url

POSIX = Namespace('http://www.w3.org/ns/posix/stat#')
LDP = Namespace("http://www.w3.org/ns/ldp#")
container_types = [URIRef('http://www.w3.org/ns/ldp#Container'), URIRef('http://www.w3.org/ns/ldp#BasicContainer')]


# FIXME
# def parse_folder_response(folder_response: Response, url) -> FolderData:
# def parse_folder_response(folder_response: Response, url, base_read_url):
#     return _parse_folder_response(folder_response.text, url, base_read_url)

# get ttl text directly
def parse_folder_response(text, url, pod):
    # print(text)
    from connector.solid_api import FolderData, Item
    g = Graph().parse(data=text, publicID=url, format='turtle')

    def is_type(sub, type) -> bool:
        return (sub, RDF.type, type) in g

    def is_container(sub) -> bool:
        for ct in container_types:
            if is_type(sub, ct):
                return True
        return False

    # get size of the files
    def get_item_size(i):
        file_uri = URIRef(i)
        try:
            o = g.objects(subject=file_uri, predicate=POSIX.size)
            s = size(int(next(o)))
        except:
            s = None
        return s

    this = URIRef(url)

    if not is_container(this):
        return False
        #  raise Exception('Not a container.')

    folders, files = [], []
    item = Item()  # create parent item
    item.name = '../'  # get_item_name(this) Parent url
    if url == pod:
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
