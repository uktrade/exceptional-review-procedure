import captcha.fields
from directory_components import forms

import django.forms


TypedChoiceField = forms.field_factory(django.forms.TypedChoiceField)
ReCaptchaField = forms.field_factory(captcha.fields.ReCaptchaField)


class BindNestedFormMixin:
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for name, field in self.fields.items():
            if isinstance(field, RadioNested):
                nested_form = field.nested_form_class(*args, **kwargs)
                # require the nested fields to be provided if the parent field is checked
                if field.coerce(self[name].data) != field.nested_form_choice:
                    for item in nested_form.fields.values():
                        item.required = False
                field.bind_nested_form(nested_form)


class RadioNestedWidget(forms.RadioSelect):
    option_template_name = 'core/nested-radio-widget.html'

    def create_option(self, *args, **kwargs):
        return {
            **super().create_option(*args, **kwargs),
            'nested_form': self.nested_form,
            'nested_form_choice': self.nested_form_choice,
        }

    def bind_nested_form(self, form):
        self.nested_form = form


class RadioNested(TypedChoiceField):
    MESSAGE_FORM_MIXIN = 'This field requires the form to use core.forms.BindNestedFormMixin'

    def __init__(self, nested_form_class=None, nested_form_choice=True, *args, **kwargs):
        self.nested_form_class = nested_form_class
        self.nested_form_choice = nested_form_choice
        super().__init__(
            widget=RadioNestedWidget,
            container_css_classes='form-group radio-nested-container',
            *args,
            **kwargs
        )
        self.widget.nested_form_choice = nested_form_choice

    def bind_nested_form(self, form):
        self.nested_form = form
        self.widget.bind_nested_form(form)

    def validate(self, value):
        super().validate(value)
        if value and not self.nested_form.is_valid():
            # trigger the form to mark the field as invalid. the nested form will then render the real errors
            raise django.forms.ValidationError(message='')

    def get_bound_field(self, form, field_name):
        assert isinstance(form, BindNestedFormMixin), self.MESSAGE_FORM_MIXIN
        return super().get_bound_field(form, field_name)


class SelectMultipleAutocomplete(django.forms.SelectMultiple):
    class Media:
        css = {
            'all': ('directory_components/js/vendor/accessible-autocomplete.min.css',)
        }
        js = (
            'directory_components/js/vendor/accessible-autocomplete.min.js',
            'js/mutliselect-autocomplete.js',
        )


class MultipleChoiceAutocomplateField(forms.MultipleChoiceField):
    def __init__(self, *args, **kwargs):
        super().__init__(
            container_css_classes='multi-select-autocomplete form-group',
            widget=SelectMultipleAutocomplete,
            *args,
            **kwargs,
        )
