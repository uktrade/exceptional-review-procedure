import captcha.fields
from directory_components import forms
from directory_constants import choices, urls
from directory_forms_api_client.forms import GovNotifyEmailActionMixin

from django.forms import Textarea
from django.utils.safestring import mark_safe

from core import constants


TERMS_LABEL = mark_safe(
    'I accept the <a href="#" target="_blank">terms and conditions</a> of the gov.uk service.'
)
INDUSTRY_CHOICES = (
    (('', 'Please select'),) + choices.INDUSTRIES + (('OTHER', 'Other'),)
)
TURNOVER_CHOICES = (
    ('0-25k', 'under £25,000'),
    ('25k-100k', '£25,000 - £100,000'),
    ('100k-1m', '£100,000 - £1,000,000'),
    ('1m-5m', '£1,000,000 - £5,000,000'),
    ('5m-25m', '£5,000,000 - £25,000,000'),
    ('25m-50m', '£25,000,000 - £50,000,000'),
    ('50m+', '£50,000,000+')
)


class ReCaptchaField(forms.DirectoryComponentsFieldMixin, captcha.fields.ReCaptchaField):
    pass


class LocationRoutingForm(forms.Form):
    CHOICES = (
        (constants.UK_BUSINESS, "I'm a UK business importing from overseas"),
        (constants.UK_CONSUMER, "I'm a UK consumer or consumer group"),
        (constants.FOREIGN, "I'm an exporter from a developed country"),

    )
    choice = forms.ChoiceField(
        label='',
        widget=forms.RadioSelect(),
        choices=CHOICES,
    )


class ProductSearchForm(forms.Form):
    product = forms.CharField(
        label='Start typing the product name or commodity code.',
        help_text='A commodity code is a way of classifying a product for import and export.'
    )


class BusinessChangeForm(forms.Form):
    sale_volume_actual = forms.CharField(label='Actual', required=False)
    sale_volume_expected = forms.CharField(label='Expected', required=False)

    production_levels_actual = forms.CharField(label='Actual', required=False)
    production_levels_expected = forms.CharField(label='Expected', required=False)

    profitability_actual = forms.CharField(label='Actual', required=False)
    profitability_expected = forms.CharField(label='Expected', required=False)

    employment_actual = forms.CharField(label='Actual', required=False)
    employment_expected = forms.CharField(label='Expected', required=False)


class TariffRelatedCommentForm(forms.Form):
    other_tariff_related_changes = forms.CharField(
        label="Do not include any sensitive or personal information. If you're unsure, leave this blank",
        widget=Textarea(attrs={'rows': 6}),
        required=False,
    )


class NonTariffRelatedCommentForm(forms.Form):
    other_non_tariff_related_changes = forms.CharField(
        label="Do not include any sensitive or personal information. If you're unsure, leave this blank",
        widget=Textarea(attrs={'rows': 6}),
        required=False,
    )


class OutcomeForm(forms.Form):
    CHOICES = (
        (constants.INCREASE, "I want an increase in the tariff rate"),
        (constants.DECREASE, "I want a decrease in the tariff rate"),
        (constants.QUOTA_CHANGE, "I want the tariff quote changed"),
        (constants.OTHER, 'Other')
    )
    outcome = forms.ChoiceField(
        label='',
        widget=forms.RadioSelect(),
        choices=CHOICES,
    )


class CompaniesHouseBusinessDetailsForm(forms.Form):
    company_name = forms.CharField(label='Registered company name')
    company_number = forms.CharField(
        required=False,
        container_css_classes='border-active-blue read-only-input-container js-disabled-only'
    )
    sector = forms.ChoiceField(
        label='Which industry are you in?',
        choices=INDUSTRY_CHOICES,
        container_css_classes='govuk-!-margin-top-6 govuk-!-margin-bottom-6',
    )
    percentage_uk_market = forms.CharField(
        label='What percentage of the total UK market do your sales represent? (optional)',
        required=False,
    )
    employees = forms.ChoiceField(
        label='Number of employees',
        choices=choices.EMPLOYEES,
        required=False,
        widget=forms.RadioSelect(),
    )
    turnover = forms.ChoiceField(
        label='Annual turnover for 2018-2019',
        choices=TURNOVER_CHOICES,
        required=False,
        widget=forms.RadioSelect(),
    )


class PersonalDetailsForm(forms.Form):
    given_name = forms.CharField(label='Given name',)
    family_name = forms.CharField(label='Family name')
    email = forms.EmailField(label='Business email address')


class SummaryForm(forms.Form):
    captcha = ReCaptchaField(
        label='',
        label_suffix='',
        container_css_classes='govuk-!-margin-top-6 govuk-!-margin-bottom-6',
    )
    terms_agreed = forms.BooleanField(label=TERMS_LABEL)


class SaveForLaterForm(GovNotifyEmailActionMixin, forms.Form):
    email = forms.EmailField(label='Email address')

    def __init__(self, return_url, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.return_url = return_url

    @property
    def serialized_data(self):
        return {
            **super().serialized_data,
            'url': self.return_url,
        }
