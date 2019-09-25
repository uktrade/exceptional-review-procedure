import pytest

from django.contrib.sessions.exceptions import SuspiciousSession
from django.core.cache import cache

from core import helpers


def test_load_saved_submission_not_shared(rf):
    cache.set('wizard_wizard_foo', {
        helpers.CacheStorage.extra_data_key: {
            helpers.CacheStorage.is_shared_key: False
        }
    })
    request = rf.get('/')
    with pytest.raises(SuspiciousSession):
        helpers.load_saved_submission(request=request, key='foo')


def test_load_saved_submission_not_exist(rf):
    request = rf.get('/')
    with pytest.raises(SuspiciousSession):
        helpers.load_saved_submission(request=request, key='foo')
