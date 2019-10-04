from directory_components import forms
from directory_constants import choices
from directory_forms_api_client.forms import GovNotifyEmailActionMixin

from django.forms import Textarea, HiddenInput, TextInput
from django.utils.safestring import mark_safe

from core import constants, fields


TERMS_LABEL = mark_safe('I accept the <a href="#" target="_blank">terms and conditions</a> of the gov.uk service.')
INDUSTRY_CHOICES = (('', 'Please select'),) + choices.INDUSTRIES + (('OTHER', 'Other'),)
TURNOVER_CHOICES = (
    ('', 'Please select'),
    ('0-25k', 'under £25,000'),
    ('25k-100k', '£25,000 - £100,000'),
    ('100k-1m', '£100,000 - £1,000,000'),
    ('1m-5m', '£1,000,000 - £5,000,000'),
    ('5m-25m', '£5,000,000 - £25,000,000'),
    ('25m-50m', '£25,000,000 - £50,000,000'),
    ('50m+', '£50,000,000+')
)


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
    term = forms.CharField(
        label='',
        help_text='A commodity code is a way of classifying a product for import and export.',
        required=False,
        container_css_classes='js-enabled-only',
        widget=TextInput(attrs={'form': 'search-form'}),
    )
    commodities = forms.CharField(
        label='Commodity codes',
        help_text='Find the commodity codes via the commodity code browser. Comma separated.',
        widget=HiddenInput,
    )


class SalesVolumeBeforeBrexitForm(forms.Form):
    sales_volume_unit = forms.ChoiceField(
        label='Select a metric',
        choices=[
            ('KILOGRAM', 'kilograms (kg)'),
            ('LITRE', 'litres'),
            ('METERS', 'meters'),
            ('UNITS', 'units'),
        ],
        widget=forms.RadioSelect(),
    )
    quarter_three_2019 = forms.CharField(label='Q3 2019')
    quarter_two_2019 = forms.CharField(label='Q2 2019')
    quarter_one_2019 = forms.CharField(label='Q1 2019')
    quarter_four_2018 = forms.CharField(label='Q4 2018')


class SalesRevenueBeforeBrexitForm(forms.Form):
    quarter_three_2019 = forms.CharField(label='Q3 2019', container_css_classes='form-group prefix-pound')
    quarter_two_2019 = forms.CharField(label='Q2 2019', container_css_classes='form-group prefix-pound')
    quarter_one_2019 = forms.CharField(label='Q1 2019', container_css_classes='form-group prefix-pound')
    quarter_four_2018 = forms.CharField(label='Q4 2018', container_css_classes='form-group prefix-pound')


class SalesAfterBrexitForm(forms.Form):
    has_volume_changed = fields.RadioNested(
        label='Volume changes',
        field_if_yes=forms.ChoiceField(
            choices=[(constants.ACTUAL, 'Actual change in volume'), (constants.EXPECTED, 'Expected change in volume')],
            widget=forms.CheckboxSelectInlineLabelMultiple,
            required=False,
        )
    )
    volumes_change_comment = forms.CharField(
        label="Tell us more (optional)",
        widget=Textarea(attrs={'rows': 6}),
        required=False,
    )
    has_price_changed = fields.RadioNested(
        label='Price changes',
        field_if_yes=forms.ChoiceField(
            choices=[(constants.ACTUAL, 'Actual change in price'), (constants.EXPECTED, 'Expected change in price')],
            widget=forms.CheckboxSelectInlineLabelMultiple,
            required=False,
        )
    )
    price_change_comment = forms.CharField(
        label="Tell us more (optional)",
        widget=Textarea(attrs={'rows': 6}),
        required=False,
    )


class MarketSizeAfterBrexitForm(forms.Form):
    has_market_size_changed = fields.RadioNested(
        label='Volume changes',
        field_if_yes=forms.ChoiceField(
            choices=[(constants.ACTUAL, 'Actual change in volume'), (constants.EXPECTED, 'Expected change in volume')],
            widget=forms.CheckboxSelectInlineLabelMultiple,
            required=False,
        )
    )
    market_size_change_comment = forms.CharField(
        label="Tell us more (optional)",
        widget=Textarea(attrs={'rows': 6}),
        required=False,
    )
    has_market_price_changed = fields.RadioNested(
        label='Price changes',
        field_if_yes=forms.ChoiceField(
            choices=[(constants.ACTUAL, 'Actual change in price'), (constants.EXPECTED, 'Expected change in price')],
            widget=forms.CheckboxSelectInlineLabelMultiple,
            required=False,
        )
    )
    market_price_change_comment = forms.CharField(
        label="Tell us more (optional)",
        widget=Textarea(attrs={'rows': 6}),
        required=False,
    )


class OtherChangesAfterBrexitForm(forms.Form):
    has_other_changes = fields.RadioNested(
        label='',
        field_if_yes=forms.ChoiceField(
            choices=[(constants.ACTUAL, 'Actual change'), (constants.EXPECTED, 'Expected change')],
            widget=forms.CheckboxSelectInlineLabelMultiple,
            required=False,
        )
    )
    other_changes_comment = forms.CharField(
        label="Tell us more (optional)",
        widget=Textarea(attrs={'rows': 6}),
        required=False,
    )


class MarketSizeForm(forms.Form):
    market_size_year = forms.ChoiceField(
        label='Year (optional)',
        choices=(
            ('', 'Please select'),
            ('2019', '2019'),
            ('2018', '2018'),
            ('2017', '2017'),
        ),
        required=False
    )
    market_size = forms.CharField(
        label='Size of the market (Optional)',
        required=False,
        container_css_classes='form-group prefix-pound'
    )


class OtherInformationForm(forms.Form):
    other_information = forms.CharField(
        label='',
        widget=Textarea(attrs={'rows': 6}),
        required=False,
    )


class OutcomeForm(forms.Form):
    tariff_rate = forms.ChoiceField(
        label='Tariff rate',
        choices=[
            (constants.INCREASE, 'I want the tariff rate to increase'),
            (constants.DECREASE, 'I want the tariff rate to decrease'),
            ('N/A', 'n/a'),
        ],
        widget=forms.RadioSelect(),
    )
    tariff_quota = forms.ChoiceField(
        label='Tariff quota',
        choices=[
            (constants.INCREASE, 'I want the tariff quota to increase'),
            (constants.DECREASE, 'I want the tariff quota to decrease'),
            ('N/A', 'n/a'),
        ],
        widget=forms.RadioSelect(),
    )


class BusinessDetailsForm(forms.Form):
    company_type = forms.ChoiceField(
        label='Company type',
        label_suffix='',
        widget=forms.RadioSelect(),
        choices=(
            ('LIMITED', 'UK private or public limited company'),
            ('OTHER', 'Other type of UK organisation'),
        ),
    )
    company_name = forms.CharField(label='Company name')
    company_number = forms.CharField(
        required=False,
        container_css_classes='form-group js-disabled-only'
    )
    sector = forms.ChoiceField(
        label='Which industry are you in?',
        choices=INDUSTRY_CHOICES,
    )

    employees = forms.ChoiceField(
        label='Number of employees',
        choices=choices.EMPLOYEES,
        required=False,
    )
    turnover = forms.ChoiceField(
        label='Annual turnover for 2018-2019',
        choices=TURNOVER_CHOICES,
        required=False,
    )
    employment_regions = forms.MultipleChoiceField(
        label='Where do you employ the most people?',
        help_text='For UK businesses only',
        choices=choices.EXPERTISE_REGION_CHOICES,
        required=False,
        widget=forms.CheckboxSelectInlineLabelMultiple,
        container_css_classes='tickboxes-scroll form-group'
    )


class PersonalDetailsForm(forms.Form):
    given_name = forms.CharField(label='Given name',)
    family_name = forms.CharField(label='Family name')
    email = forms.EmailField(label='Email address')


class SummaryForm(forms.Form):
    captcha = fields.ReCaptchaField(
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
