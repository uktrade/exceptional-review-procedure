from django import template


register = template.Library()


@register.simple_tag(takes_context=True)
def get_step_url(context, step):
    view = context['view']
    assert step in view.form_list, f'"{step}" not found in "{view.url_name}"'
    url = view.get_step_url(step)
    return f'{url}?change=True'
