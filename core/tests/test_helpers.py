import pytest

from django.contrib.sessions.exceptions import SuspiciousSession

from core import helpers


def test_load_saved_submission_not_shared(rf):
    request = rf.get('/')
    with pytest.raises(SuspiciousSession):
        helpers.load_saved_submission(request=request, key='foo')
