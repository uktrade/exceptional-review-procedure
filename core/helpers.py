import uuid
from formtools.wizard.storage.base import BaseStorage

from django.core.cache import cache
from django.utils.datastructures import MultiValueDict


CACHE_KEY_USER = 'wizard-user-cache-key'


class CacheStorage(BaseStorage):

    def __init__(self, prefix, request=None, file_storage=None):
        self.request = request
        if not self.user_cache_key:
            self.user_cache_key = str(uuid.uuid4())
        super().__init__(prefix=f'{prefix}_{self.user_cache_key}', request=request, file_storage=file_storage)
        if not self.data:
            self.init_data()

    @property
    def data(self):
        return cache.get(self.prefix)

    @data.setter
    def data(self, value):
        cache.set(self.prefix, value, timeout=60*60*24*30)  # 30 days

    @property
    def user_cache_key(self):
        return self.request.session.get(CACHE_KEY_USER)

    @user_cache_key.setter
    def user_cache_key(self, value):
        self.request.session[CACHE_KEY_USER] = value
        self.request.session.modified = True

    def set_step_data(self, step, cleaned_data):
        if isinstance(cleaned_data, MultiValueDict):
            cleaned_data = dict(cleaned_data.lists())
        # updating a property that is a dict underneath is hairy
        data = {**self.data}
        data[self.step_data_key][step] = cleaned_data
        self.data = data

    def _set_current_step(self, step):
        # updating a property that is a dict underneath is hairy
        self.data = {**self.data, self.step_key: step}

    def _set_extra_data(self, extra_data):
        # updating a property that is a dict underneath is hairy
        self.data = {**self.data, self.extra_data_key: extra_data}
