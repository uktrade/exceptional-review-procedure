import captcha.fields
from directory_components import forms

import django.forms


TypedChoiceField = forms.field_factory(django.forms.TypedChoiceField)
ReCaptchaField = forms.field_factory(captcha.fields.ReCaptchaField)


class RadioNestedWidget(forms.RadioSelect):
    option_template_name = 'core/nested-radio-widget.html'

    def create_option(self, *args, **kwargs):
        option = super().create_option(*args, **kwargs)
        option['field_if_yes'] = self.field_if_yes
        option['field_if_no'] = self.field_if_no
        return option


class RadioNested(TypedChoiceField):
    def __init__(self, field_if_yes=None, field_if_no=None, *args, **kwargs):
        self.field_if_yes = field_if_yes
        self.field_if_no = field_if_no
        super().__init__(
            coerce=lambda x: x == 'True',
            choices=[(True, 'Yes'), (False, 'No')],
            widget=RadioNestedWidget,
            container_css_classes='radio-nested-container',
            *args, **kwargs
        )

    def get_bound_field(self, form, name):
        if self.field_if_yes:
            self.widget.field_if_yes = self.field_if_yes.get_bound_field(form, f'{name}_yes')
        else:
            self.widget.field_if_yes = None
        if self.field_if_no:
            self.widget.field_if_no = self.field_if_no.get_bound_field(form, f'{name}_no')
        else:
            self.widget.field_if_no = None
        return super().get_bound_field(form, name)
