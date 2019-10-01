from unittest import mock

import pytest

from django.contrib.sessions.exceptions import SuspiciousSession
from django.core.cache import cache
from django.shortcuts import Http404

from core import helpers


def test_load_saved_submission_not_shared(rf):
    submission = {helpers.CacheStorage.extra_data_key: {helpers.CacheStorage.is_shared_key: False}}
    cache.set('wizard_wizard_foo', submission, 60)
    request = rf.get('/')
    with pytest.raises(SuspiciousSession):
        helpers.load_saved_submission(request=request, key='foo')


def test_load_saved_submission_shared(rf, client):
    request = rf.get('/')
    request.session = client.session
    submission = {helpers.CacheStorage.is_shared_key: True}
    cache.set('wizard_wizard_bar', {helpers.CacheStorage.extra_data_key: submission}, 60)

    helpers.load_saved_submission(request=request, key='bar')

    assert helpers.get_user_cache_key(request) == 'bar'


def test_load_saved_submission_not_exist(rf, client):
    request = rf.get('/')
    request.session = client.session
    with pytest.raises(Http404):
        helpers.load_saved_submission(request=request, key='wolf')


@mock.patch('requests.get')
def test_lookup_commodity_code_by_name(mock_get, settings):
    helpers.lookup_commodity_code_by_name('thing', page=2)

    assert mock_get.call_count == 1
    assert mock_get.call_args == mock.call(settings.COMMODITY_NAME_SEARCH_API_ENDPOINT, {'q': 'thing', 'page': 2})
