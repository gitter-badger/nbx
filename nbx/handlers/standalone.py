import os.path

from tornado import web

import IPython
from nbx.handlers import NBXHandler
import nbx.kernel_client as kernel_client
from IPython.html.base.handlers import notebook_path_regex

CODE_FMT = """
from nbx.handlers.standalone import get_html
get_html({html_obj}, "{attr}")
"""

def autolink(obj):
    """
    Output a standalone link to a named variable bound to this object
    """
    name = get_varname(obj)
    return link(name)

def link(html_obj, link_name=None):
    """
    Use a Javascript Object so we can output the link using href and not onclick
    """
    from IPython.core.display import Javascript
    if link_name is None:
        link_name = html_obj
    js = """
    (function() {{
        // https://github.com/ipython/ipython/issues/5293
        if(typeof(toinsert) != 'undefined') {{
            element = toinsert;
        }}
        var notebook = IPython.notebook;
        var utils = IPython.utils;
        var path = notebook.notebook_path;
        var nbname = notebook.notebook_name;
        var link_href = utils.url_join_encode(
            notebook.base_url,
            "standalone",
            path,
            nbname,
            "{html_obj}"
        )
        toinsert.append('<a target="_new" href="'+link_href+'">{link_name}</a>');
    }})()
    """.format(html_obj=html_obj, link_name=link_name)
    return Javascript(data=js)

def get_varname(obj):
    """
    Try to get the variable that this object is
    bound to in the IPython kernel
    """
    inst = IPython.InteractiveShell._instance
    for k,v in inst.user_ns.items():
        if v is obj and not k.startswith('_'):
            return k

def get_html(html_obj, attr):
    if hasattr(html_obj, 'html_obj'):
        html_obj = getattr(html_obj, 'html_obj')

    if hasattr(html_obj, attr):
        html = getattr(html_obj, attr)

    try:
        html = html_obj[attr]
    except:
        pass

    if callable(html):
        html = html()

    return html

class DirectoryHtml(object):
    """
    An HTMLObject that refences a directory
    """
    def __init__(self, dir, default=None):
        self.dir = dir
        self.default = default

    def __getitem__(self, key):
        path = os.path.join(self.dir, key)
        if os.path.exists(path):
            with open(path) as f:
                html = f.read()
            return html
        raise KeyError()

    def to_html(self):
        if self.default:
            return self[self.default]

class StandaloneHandler(NBXHandler):
    @web.authenticated
    def get(self, path, name, html_obj, attr=None):
        if not attr:
            self.redirect(self.request.path + '/to_html')
            return

        print(path, html_obj, attr)
        # path shouldn't have preceding /.
        # session.js creates session with notebook model.
        if path.startswith('/'):
            path = path[1:]
        sm = self.session_manager
        session = sm.get_session(path=path, name=name)
        kernel_id = session['kernel']['id']

        km = self.kernel_manager
        client = km.get_kernel(kernel_id).client()
        client = kernel_client.KernelClient(client)

        code = CODE_FMT.format(html_obj=html_obj, attr=attr);
        data = client.execute(code)
        client.exit()

        html = '';
        if 'text/plain' in data:
            html = eval(data['text/plain'])

        self.finish(html)

_html_obj = r"(?P<html_obj>[\w-]+)"
_attr = r"(?P<attr>[.\w-]+)"

default_handlers = [
    (r"/standalone%s/%s" % (notebook_path_regex, _html_obj), StandaloneHandler),
    (r"/standalone%s/%s/%s" % (notebook_path_regex, _html_obj, _attr), StandaloneHandler),
]
