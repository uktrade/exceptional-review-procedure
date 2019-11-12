from unittest import mock

import pytest

from django.contrib.sessions.exceptions import SuspiciousSession
from django.core.cache import cache
from django.http import HttpRequest
from django.shortcuts import Http404

from core import helpers


def test_load_saved_submission_not_shared(rf):
    submission = {helpers.CacheStorage.extra_data_key: {helpers.CacheStorage.is_shared_key: False}}
    cache.set('wizard_business_wizard_foo', submission, 60)
    request = rf.get('/')
    with pytest.raises(SuspiciousSession):
        helpers.load_saved_submission(request=request, prefix='business_wizard', key='foo')


def test_load_saved_submission_shared(rf, client):
    request = rf.get('/')
    request.session = client.session
    submission = {helpers.CacheStorage.is_shared_key: True}
    cache.set('wizard_business_wizard_bar', {helpers.CacheStorage.extra_data_key: submission}, 60)

    helpers.load_saved_submission(request=request, prefix='business_wizard', key='bar')

    assert helpers.get_user_cache_key(request) == 'bar'


def test_load_saved_submission_not_exist(rf, client):
    request = rf.get('/')
    request.session = client.session
    with pytest.raises(Http404):
        helpers.load_saved_submission(request=request, prefix='business_wizard', key='wolf')


@mock.patch('requests.get')
def test_search_commodity_by_term(mock_get):
    helpers.search_commodity_by_term('thing', page=2)

    assert mock_get.call_count == 1
    assert mock_get.call_args == mock.call(helpers.COMMODITY_SEARCH_BY_TERM_URL, {'q': 'thing', 'page': 2})


@mock.patch('requests.get')
def test_search_commodity_by_code(mock_get):
    helpers.search_commodity_by_code('17')

    assert mock_get.call_count == 1
    assert mock_get.call_args == mock.call(helpers.COMMODITY_SEARCH_BY_CODE_URL, {'q': '17'})


@mock.patch('requests.get')
def test_search_hierarchy(mock_get):
    helpers.search_hierarchy('17')

    assert mock_get.call_count == 1
    assert mock_get.call_args == mock.call(helpers.HIERARCHY_SEARCH_URL, {'node_id': '17', 'country_code': 'dj'})


def test_get_sender_ip():
    request = HttpRequest()
    request.META = {'REMOTE_ADDR': '192.168.93.2'}
    ip_address = helpers.get_sender_ip_address(request)
    assert ip_address == '192.168.93.2'


def test_get_sender_no_ip():
    request = HttpRequest()
    assert helpers.get_sender_ip_address(request) is None
