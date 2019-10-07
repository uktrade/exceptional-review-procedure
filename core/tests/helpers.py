from formtools.wizard.views import normalize_name
import requests

from django.urls import resolve, reverse


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
    view_name = normalize_name(view_class.__name__)

    def submit_step(data, step_name=None):
        step_name = step_name or next(step_names)
        url = reverse(url_name, kwargs={'step': step_name})
        data = {key if key in no_transform else f'{step_name}-{key}': value for key, value in data.items()}
        data[view_name + '-current_step'] = step_name
        return client.post(url, data)
    return submit_step
