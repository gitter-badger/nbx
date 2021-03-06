import datetime
import os.path

from IPython.html.services.contents.manager import ContentsManager
from IPython.html.utils import url_path_join

from .dispatch import DispatcherMixin

def _fullpath(name, path):
    fullpath = url_path_join(path, name)
    return fullpath

class BackwardsCompatMixin(object):
    # shims to bridge Content service and older notebook apis
    def get_model_dir(self, name, path='', content=True):
        """ retrofit to use old list_dirs. No notebooks """
        model = self._base_model(name, path)
        fullpath = self.fullpath(name, path)

        model['type'] = 'directory'
        dirs = self.list_dirs(fullpath)
        notebooks = self.list_notebooks(fullpath)
        entries = list(dirs) + list(notebooks)
        model['content'] = entries
        return model

    def get_model_notebook(self, name, path='', content=True, **kwargs):
        return self.get_notebook(name, path, content=content, **kwargs)

    def file_exists(self, name, path=''):
        # in old version, only file is notebook
        ret =  self.notebook_exists(name, path)
        return ret

    def is_notebook(self, path):
        """
        Note that is_notebook is a nbx method, it's in BackwardsCompatMixin
        because it uses old api

        split path into name, path and use notebook_exists
        """
        path, name = os.path.split(path)
        ret =  self.notebook_exists(name, path)
        return ret

    def is_dir(self, path):
        """
        nbx api method.
        """
        return self.path_exists(path) and not self.is_notebook(path)


class NBXContentsManager(DispatcherMixin, ContentsManager):
    def __init__(self, *args, **kwargs):
        super(NBXContentsManager, self).__init__(*args, **kwargs)

    def is_dir(self, path):
        raise NotImplementedError('must be implemented in a subclass')

    def is_notebook(self, path):
        return path.endswith('.ipynb')

    def _base_model(self, name, path=''):
        """Build the common base of a contents model"""
        # Create the base model.
        model = {}
        model['name'] = name
        model['path'] = path
        model['created'] = datetime.datetime.now()
        model['last_modified'] = datetime.datetime.now()
        model['content'] = None
        model['format'] = None
        return model

    def fullpath(self, name, path):
        return _fullpath(name, path)
