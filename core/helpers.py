from urllib.parse import urlencode, urljoin
import uuid

from directory_components import forms
from formtools.wizard.storage.base import BaseStorage
from formtools.wizard.storage.session import SessionStorage
import requests

from django.conf import settings
from django.contrib.sessions.exceptions import SuspiciousSession
from django.core.cache import cache
from django.shortcuts import Http404

from core import constants, fields


CACHE_KEY_USER = 'wizard-user-cache-key'
COMMODITY_SEARCH_BY_CODE_URL = urljoin(settings.DIT_HELPDESK_URL, '/search/api/commodity-code/')
COMMODITY_SEARCH_BY_TERM_URL = urljoin(settings.DIT_HELPDESK_URL, '/search/api/commodity-term/')
HIERARCHY_SEARCH_URL = urljoin(settings.DIT_HELPDESK_URL, '/search/api/hierarchy/')


class NoResetStorage(SessionStorage):
    def reset(self):
        pass


class PersistStepsMixin:

    steps = [constants.STEP_PERSONAL, constants.STEP_BUSINESS]

    def init_data(self):
        persist = {}
        if self.data:
            for step in self.steps:
                if step in self.data[self.step_data_key]:
                    persist[step] = self.data[self.step_data_key][step]
        super().init_data()
        self.data[self.step_data_key] = persist


class SharableCacheEntryMixin:
    def init_data(self):
        super().init_data()
        self.extra_data[self.is_shared_key] = False

    def mark_shared(self):
        self.extra_data[self.is_shared_key] = True


class CacheStorage(SharableCacheEntryMixin, PersistStepsMixin, BaseStorage):

    is_shared_key = 'is_shared'

    def __init__(self, prefix, request=None, file_storage=None, *args, **kwargs):
        key = get_user_cache_key(request)
        if not key:
            key = str(uuid.uuid4())
            set_user_cache_key(request=request, key=key)
        super().__init__(prefix=f'{prefix}_{key}', request=request, file_storage=file_storage, *args, **kwargs)
        self.data = self.load_data()
        if not self.data:
            self.init_data()

    def load_data(self):
        return cache.get(self.prefix)

    def update_response(self, response):
        super().update_response(response)
        cache.set(self.prefix, self.data, timeout=settings.SAVE_FOR_LATER_EXPIRES_SECONDS)


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


def search_commodity_by_code(code):
    return requests.get(COMMODITY_SEARCH_BY_CODE_URL, {'q': code})


def search_commodity_by_term(term, page):
    return requests.get(COMMODITY_SEARCH_BY_TERM_URL, {'q': term, 'page': page})


def search_hierarchy(node_id):
    # the API needs country code but it will not affect the hierarchy for our use case, so hard-code it
    return requests.get(HIERARCHY_SEARCH_URL, {'node_id': node_id, 'country_code': 'dj'})


def get_paginator_url(filters, url):
    querystring = urlencode({
        key: value
        for key, value in filters.lists()
        if value and key != 'page'
    }, doseq=True)
    return f'{url}?{querystring}'


def get_form_display_data(form):
    if not form.is_valid():
        return dict.fromkeys(form.fields.keys(), '-')
    display_data = {**form.cleaned_data}
    for name, value in form.cleaned_data.items():
        field = form.fields[name]
        # note the isinstance may not be mutually exclusive. some fields hit multiple. this is desirable.
        if isinstance(field, fields.RadioNested):
            display_data.update(get_form_display_data(field.nested_form))
        if isinstance(field, forms.MultipleChoiceField):
            display_data[name] = get_choices_labels(form=form, field_name=name)
        if isinstance(field, forms.ChoiceField):
            display_data[name] = get_choice_label(form=form, field_name=name)
        if isinstance(field, fields.TypedChoiceField):
            display_data[name] = get_choice_label(form=form, field_name=name)
    return display_data


def get_choice_label(form, field_name):
    choices = dict(form.fields[field_name].choices)
    value = form.cleaned_data[field_name]
    return choices.get(value)


def get_choices_labels(form, field_name):
    choices = dict(form.fields[field_name].choices)
    value = form.cleaned_data[field_name]
    return [choices[item] for item in value]
