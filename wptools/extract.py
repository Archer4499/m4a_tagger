"""
WPTools Extract module.
"""

import json

from .fetch import get_parsetree
from collections import defaultdict
from lxml import etree


def get_infobox(title):
    data = get_parsetree(title)
    ptree = parsetree(data)
    for item in etree.fromstring(ptree).xpath("//template"):
        if "box" in item.find('title').text:
            return template_to_dict(item)


def parsetree(data):
    """return parsetree XML from API JSON"""
    try:
        data = json.loads(data)
        ptree = data["parse"]["parsetree"]["*"]
        data_etree = etree.fromstring(ptree).xpath("//text()")
        title = data["parse"]["title"]

        # return DISAMBIGUATION if found
        for item in data_etree:
            if 'may refer to:' in item:
                return "DISAMBIGUATION " + title

        # return #REDIRECT text from query if extant
        for item in data_etree:
            if item.startswith("#REDIRECT"):
                return item.strip()

        return ptree
    except:
        return json.loads(data)["error"]["info"]


def template_to_dict(tree):
    """returns wikitext template as dict (one deep)"""
    obj = defaultdict(str)
    for item in tree:
        try:
            name = item.findtext('name')
            tmpl = item.find('value').find('template')
            if tmpl is not None:
                value = etree.tostring(tmpl, encoding="unicode")
            else:
                value = item.findtext('value')
            if name and value:
                obj[name.strip()] = value.strip()
        except:
            obj[__name__ + " ERROR"] = etree.tostring(item, encoding="unicode")
    return dict(obj)
