from urllib.parse import urlencode
import uuid

from formtools.wizard.storage.base import BaseStorage
from formtools.wizard.storage.session import SessionStorage
import requests

from django.conf import settings
from django.contrib.sessions.exceptions import SuspiciousSession
from django.core.cache import cache
from django.shortcuts import Http404


CACHE_KEY_USER = 'wizard-user-cache-key'
# unusual character that is unlikely to be included in each product label
PRODUCT_DELIMITER = 'µ'


class NoResetStorage(SessionStorage):
    def reset(self):
        pass


class CacheStorage(BaseStorage):

    is_shared_key = 'is_shared'

    def __init__(self, prefix, request=None, file_storage=None):
        key = get_user_cache_key(request)
        if not key:
            key = str(uuid.uuid4())
            set_user_cache_key(request=request, key=key)
        super().__init__(prefix=f'{prefix}_{key}', request=request, file_storage=file_storage)
        self.data = self.load_data()
        if not self.data:
            self.init_data()

    def init_data(self):
        super().init_data()
        self.extra_data[self.is_shared_key] = False

    def load_data(self):
        return cache.get(self.prefix)

    def update_response(self, response):
        super().update_response(response)
        cache.set(self.prefix, self.data, timeout=60*60*72)  # 72 hours

    def mark_shared(self):
        self.extra_data[self.is_shared_key] = True


def get_user_cache_key(request):
    return request.session.get(CACHE_KEY_USER)


def set_user_cache_key(request, key):
    request.session[CACHE_KEY_USER] = key
    request.session.modified = True


def load_saved_submission(request, prefix, key):
    submission = cache.get(f'wizard_{prefix}_{key}')
    if not submission:
        raise Http404
    elif not submission[CacheStorage.extra_data_key][CacheStorage.is_shared_key]:
        raise SuspiciousSession
    else:
        set_user_cache_key(request, key)


def lookup_commodity_code_by_name(query, page):
    return requests.get(settings.COMMODITY_NAME_SEARCH_API_ENDPOINT, {'q': query, 'page': page})


def search_hierarchy(node_id):
    # the API needs country code but it will not affect the hierarchy for our use case, so hard-code it
    return requests.get(settings.HIERARCHY_BROWSER_LOOKUP_API_ENDPOINT, {'node_id': node_id, 'country_code': 'dj'})


def get_paginator_url(filters, url):
    querystring = urlencode({
        key: value
        for key, value in filters.lists()
        if value and key != 'page'
    }, doseq=True)
    return f'{url}?{querystring}'


def parse_commodities(commodities):
    return commodities.split(PRODUCT_DELIMITER) if commodities else []
