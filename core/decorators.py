from functools import wraps

from django.conf import settings
from django.http import HttpResponseNotFound


def holding_page_redirect(view_function):

    @wraps(view_function)
    def _wrapped_view_function(request, *args, **kwargs):
        if settings.FEATURE_FLAGS['SERVICE_HOLDING_PAGE_ON']:
            return HttpResponseNotFound()

        return view_function(request, *args, **kwargs)

    return _wrapped_view_function
