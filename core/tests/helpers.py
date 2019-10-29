from importlib import import_module, reload
import sys

import requests

from django.conf import settings
from django.urls import clear_url_caches, resolve, reverse


no_transform = [
    'g-recaptcha-response',
    'wizard_save_for_later',
    'wizard_select_product',
    'wizard_browse_product',
    'wizard_remove_selected_product',
]


def create_response(json_body={}, status_code=200, content=None):
    response = requests.Response()
    response.status_code = status_code
    response.json = lambda: json_body
    response._content = content
    return response


def submit_step_factory(client, url_name):
    view_class_match = resolve(reverse(url_name, kwargs={'step': None}))
    view_class = view_class_match.func.view_class
    step_names = iter([name for name, form in view_class.form_list])
    view = view_class()
    prefix = view.get_prefix(None)

    def submit_step(data, step_name=None):
        step_name = step_name or next(step_names)
        url = reverse(url_name, kwargs={'step': step_name})
        data = build_wizard_data_shape(data=data, prefix=prefix, step_name=step_name)
        return client.post(url, data)
    return submit_step


def build_wizard_data_shape(data, prefix, step_name):
    data = {key if key in no_transform else f'{step_name}-{key}': value for key, value in data.items()}
    data[f'{prefix}-current_step'] = step_name
    return data


def reload_urlconf(urlconf=None):
    clear_url_caches()
    if urlconf is None:
        urlconf = settings.ROOT_URLCONF
    if urlconf in sys.modules:
        reload(sys.modules[urlconf])
    else:
        import_module(urlconf)
