from directory_components import forms
from directory_constants import choices
from directory_forms_api_client.forms import GovNotifyEmailActionMixin

from django.forms import Textarea, HiddenInput, TextInput
from django.utils.safestring import mark_safe

from core import constants, fields

OTHER = 'OTHER'
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
SALES_VOLUME_UNIT_CHOICES = [
    ('KILOGRAM', 'kilograms (kg)'),
    ('LITRE', 'litres'),
    ('METERS', 'meters'),
    ('UNITS', 'units (number of items)'),
    (OTHER, 'Other')
]
COMPANY_TYPE_CHOICES = (
    ('LIMITED', 'UK private or public limited company'),
    ('OTHER', 'Other type of UK organisation'),
)
CHOICES_CHANGE_TYPE_VOLUME = (
    (constants.ACTUAL, 'Actual change in volume'),
    (constants.EXPECTED, 'Expected change in volume')
)
CHOICES_CHANGE_TYPE_PRICE = (
    (constants.ACTUAL, 'Actual change in price'),
    (constants.EXPECTED, 'Expected change in price')
)
CHOICES_CHANGE_TYPE = (
    (constants.ACTUAL, 'Actual change'),
    (constants.EXPECTED, 'Expected change')
)
CHOICES_CHANGE_TYPE_CHOICE = (
    (constants.ACTUAL, 'Actual change in choice'),
    (constants.EXPECTED, 'Expected change in choice')
)


def get_display_data(form):
    assert form.is_valid()
    display_data = {**form.cleaned_data}
    for name, value in form.cleaned_data.items():
        field = form.fields[name]
        # note the isinstance may not be mutually exclusive. some fields hit multiple. this is desirable.
        if isinstance(field, fields.RadioNested):
            display_data.update(get_display_data(field.nested_form))
        if isinstance(field, forms.MultipleChoiceField):
            display_data[name] = get_choices_labels(form=form, field_name=name)
        if isinstance(field, forms.ChoiceField):
            display_data[name] = get_choice_label(form=form, field_name=name)
        if isinstance(field, fields.TypedChoiceField):
            display_data[name] = get_choice_label(form=form, field_name=name)
    return display_data


def get_choice_label(form, field_name):
    choices = dict(form.fields[field_name].choices)
    value = form.cleaned_data[field_name]
    return choices.get(value)


def get_choices_labels(form, field_name):
    choices = dict(form.fields[field_name].choices)
    value = form.cleaned_data[field_name]
    return [choices[item] for item in value]


class ConsumerChoiceChangeForm(forms.Form):
    choice_change_type = forms.MultipleChoiceField(
        label='',
        choices=CHOICES_CHANGE_TYPE_CHOICE,
        widget=forms.CheckboxSelectInlineLabelMultiple,
    )
    choice_change_comment = forms.CharField(
        label="Tell us more",
        widget=Textarea(attrs={'rows': 6}),
    )


class VolumeChangeForm(forms.Form):
    volume_changed_type = forms.MultipleChoiceField(
        label='',
        choices=CHOICES_CHANGE_TYPE_VOLUME,
        widget=forms.CheckboxSelectInlineLabelMultiple,
    )
    volumes_change_comment = forms.CharField(
        label="Tell us more",
        widget=Textarea(attrs={'rows': 6}),
    )


class PriceChangeForm(forms.Form):
    price_changed_type = forms.MultipleChoiceField(
        label='',
        choices=CHOICES_CHANGE_TYPE_PRICE,
        widget=forms.CheckboxSelectInlineLabelMultiple,
    )
    price_change_comment = forms.CharField(
        label="Tell us more",
        widget=Textarea(attrs={'rows': 6}),
    )


class MarketSizeChangeForm(forms.Form):
    market_size_changed_type = forms.MultipleChoiceField(
        label='',
        choices=CHOICES_CHANGE_TYPE_VOLUME,
        widget=forms.CheckboxSelectInlineLabelMultiple,
    )
    market_size_change_comment = forms.CharField(
        label="Tell us more",
        widget=Textarea(attrs={'rows': 6}),
    )


class MarketPriceChangeForm(forms.Form):
    market_price_changed_type = forms.MultipleChoiceField(
        label='',
        choices=CHOICES_CHANGE_TYPE_PRICE,
        widget=forms.CheckboxSelectInlineLabelMultiple,
    )
    market_price_change_comment = forms.CharField(
        label="Tell us more",
        widget=Textarea(attrs={'rows': 6}),
    )


class OtherChangesForm(forms.Form):
    has_other_changes_type = forms.MultipleChoiceField(
        label='',
        choices=CHOICES_CHANGE_TYPE,
        widget=forms.CheckboxSelectInlineLabelMultiple,
    )
    other_changes_comment = forms.CharField(
        label="Tell us more",
        widget=Textarea(attrs={'rows': 6}),
    )


class MarketSizeDetailsForm(forms.Form):
    market_size_year = forms.ChoiceField(
        label='Financial year',
        help_text='Give the most recent data you can.',
        choices=(
            ('', 'Please select'),
            ('2019', '2019'),
            ('2018', '2018'),
            ('2017', '2017'),
        ),
    )
    market_size = forms.IntegerField(
        label='Market value',
        container_css_classes='form-group prefix-pound',
    )


class RoutingUserTypeForm(forms.Form):
    CHOICES = (
        (constants.UK_BUSINESS, "I'm a UK business importing from overseas"),
        (constants.UK_CONSUMER, "I'm a UK consumer or consumer group"),
        (constants.DEVELOPING_COUNTRY_COMPANY, "I'm an exporter from a developing country"),
    )
    choice = forms.ChoiceField(
        label='',
        widget=forms.RadioSelect(),
        choices=CHOICES,
    )


class RoutingImportFromOverseasForm(forms.Form):
    choice = fields.TypedChoiceField(
        label='',
        coerce=lambda x: x == 'True',
        choices=[(True, 'Yes'), (False, 'No')],
        widget=forms.RadioSelect,
    )


class ProductSearchForm(forms.Form):
    MESSAGE_MISSING_PRODUCT = 'Please specify an affected product'

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

    def clean(self):
        super().clean()
        if not self.cleaned_data.get('commodities'):
            self.add_error('term', self.MESSAGE_MISSING_PRODUCT)


class OtherMetricNameForm(forms.Form):
    other_metric_name = forms.CharField(label='Metric name')


class SalesVolumeBeforeBrexitForm(fields.BindNestedFormMixin, forms.Form):
    sales_volume_unit = fields.RadioNested(
        label='Select a metric',
        choices=SALES_VOLUME_UNIT_CHOICES,
        nested_form_class=OtherMetricNameForm,
        nested_form_choice=OTHER,
    )
    quarter_three_2019_sales_volume = forms.IntegerField(label='Q3 2019')
    quarter_two_2019_sales_volume = forms.IntegerField(label='Q2 2019')
    quarter_one_2019_sales_volume = forms.IntegerField(label='Q1 2019')
    quarter_four_2018_sales_volume = forms.IntegerField(label='Q4 2018')


class SalesRevenueBeforeBrexitForm(forms.Form):
    quarter_three_2019_sales_revenue = forms.IntegerField(
        label='Q3 2019',
        container_css_classes='form-group prefix-pound',
    )
    quarter_two_2019_sales_revenue = forms.IntegerField(
        label='Q2 2019',
        container_css_classes='form-group prefix-pound',
    )
    quarter_one_2019_sales_revenue = forms.IntegerField(
        label='Q1 2019',
        container_css_classes='form-group prefix-pound',
    )
    quarter_four_2018_sales_revenue = forms.IntegerField(
        label='Q4 2018',
        container_css_classes='form-group prefix-pound',
    )


class SalesAfterBrexitForm(fields.BindNestedFormMixin, forms.Form):
    has_volume_changed = fields.RadioNested(
        label='Volume changes',
        nested_form_class=VolumeChangeForm,
        coerce=lambda x: x == 'True',
        choices=[(True, 'Yes'), (False, 'No')],
    )
    has_price_changed = fields.RadioNested(
        label='Price changes',
        nested_form_class=PriceChangeForm,
        coerce=lambda x: x == 'True',
        choices=[(True, 'Yes'), (False, 'No')],
    )


class MarketSizeAfterBrexitForm(fields.BindNestedFormMixin, forms.Form):
    has_market_size_changed = fields.RadioNested(
        label='Volume changes',
        nested_form_class=MarketSizeChangeForm,
        coerce=lambda x: x == 'True',
        choices=[(True, 'Yes'), (False, 'No')],
    )
    has_market_price_changed = fields.RadioNested(
        label='Price changes',
        nested_form_class=MarketPriceChangeForm,
        coerce=lambda x: x == 'True',
        choices=[(True, 'Yes'), (False, 'No')],
    )


class OtherChangesAfterBrexitForm(fields.BindNestedFormMixin, forms.Form):
    has_other_changes = fields.RadioNested(
        label='',
        nested_form_class=OtherChangesForm,
        coerce=lambda x: x == 'True',
        choices=[(True, 'Yes'), (False, 'No')],
    )


class MarketSizeForm(fields.BindNestedFormMixin, forms.Form):
    market_size_known = fields.RadioNested(
        label='',
        nested_form_class=MarketSizeDetailsForm,
        coerce=lambda x: x == 'True',
        choices=[(True, 'Yes'), (False, 'No')],
    )


class OtherInformationForm(forms.Form):
    other_information = forms.CharField(
        label='',
        widget=Textarea(attrs={'rows': 6}),
        required=False,
    )


class OutcomeForm(fields.BindNestedFormMixin, forms.Form):
    tariff_rate = forms.ChoiceField(
        label='Tariff rate',
        choices=[
            (constants.INCREASE, 'I want the tariff rate to increase'),
            (constants.DECREASE, 'I want the tariff rate to decrease'),
            ('N/A', 'I want neither'),
        ],
        widget=forms.RadioSelect(),
    )
    tariff_quota = forms.ChoiceField(
        label='Tariff quota',
        choices=[
            (constants.INCREASE, 'I want the tariff quota to increase'),
            (constants.DECREASE, 'I want the tariff quota to decrease'),
            ('N/A', 'I want neither'),
        ],
        widget=forms.RadioSelect(),
    )


class BusinessDetailsForm(fields.BindNestedFormMixin, forms.Form):
    company_type = forms.ChoiceField(
        label='Company type',
        label_suffix='',
        widget=forms.RadioSelect(),
        choices=COMPANY_TYPE_CHOICES,
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


class ConsumerChangeForm(fields.BindNestedFormMixin, forms.Form):
    has_consumer_price_changed = fields.RadioNested(
        label='Price changes',
        nested_form_class=PriceChangeForm,
        coerce=lambda x: x == 'True',
        choices=[(True, 'Yes'), (False, 'No')],
    )
    has_consumer_choice_changed = fields.RadioNested(
        label='Choice changes',
        nested_form_class=ConsumerChoiceChangeForm,
        coerce=lambda x: x == 'True',
        choices=[(True, 'Yes'), (False, 'No')],
    )


class ConsumerGroupForm(forms.Form):
    given_name = forms.CharField(label='Given name',)
    family_name = forms.CharField(label='Family name')
    email = forms.EmailField(label='Email address')
    income_bracket = forms.CharField(
        label='Income bracket (optional)',
        required=False,
    )
    organisation_name = forms.CharField(
        label='Organisation name (optional)',
        required=False
    )
    consumer_regions = forms.MultipleChoiceField(
        label='Where are most of your consumers based?',
        help_text='For UK consumer organisations only',
        choices=choices.EXPERTISE_REGION_CHOICES,
        required=False,
        widget=forms.CheckboxSelectInlineLabelMultiple,
        container_css_classes='tickboxes-scroll form-group'
    )


class DevelopingCountryForm(forms.Form):
    country = forms.ChoiceField(
        choices=[(item, item) for item in constants.GENERALISED_SYSTEM_OF_PERFERENCE_COUNTRIES],
    )


class BusinessDetailsDevelopingCountryForm(forms.Form):
    company_type = forms.ChoiceField(
        label='Company type',
        label_suffix='',
        widget=forms.RadioSelect(),
        choices=COMPANY_TYPE_CHOICES,
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


class ImportedProductsUsageDetailsForm(forms.Form):
    imported_good_sector = forms.ChoiceField(
        label='Industry of product or service',
        choices=choices.INDUSTRIES,
    )
    imported_good_sector_details = forms.CharField(
        label="Description of products or service",
        widget=Textarea(attrs={'rows': 6}),
    )


class ImportedProductsUsageForm(fields.BindNestedFormMixin, forms.Form):
    imported_goods_makes_something_else = fields.RadioNested(
        label='',
        nested_form_class=ImportedProductsUsageDetailsForm,
        coerce=lambda x: x == 'True',
        choices=[(True, 'Yes'), (False, 'No')],
    )


class ProductionPercentageForm(forms.Form):
    production_volume_percentage = forms.IntegerField(
        label='Percentage of total production volume',
        container_css_classes='form-group suffix-percentage',
    )
    production_cost_percentage = forms.IntegerField(
        label='Percentage of total production costs',
        container_css_classes='form-group prefix-pound',
    )


class CountriesImportSourceForm(forms.Form):
    import_countries = forms.MultipleChoiceField(
        label='',
        choices=[item for item in choices.COUNTRY_CHOICES if item[0] != 'GB'],
        widget=forms.CheckboxSelectInlineLabelMultiple,
        container_css_classes='tickboxes-scroll form-group'
    )


class EquivalendUKGoodsDetailsForm(forms.Form):
    equivalent_uk_goods_details = forms.CharField(
        label="Tell us more",
        widget=Textarea(attrs={'rows': 6}),
    )


class EquivalendUKGoodsForm(fields.BindNestedFormMixin, forms.Form):
    equivalent_uk_goods = fields.RadioNested(
        label='',
        nested_form_class=EquivalendUKGoodsDetailsForm,
        coerce=lambda x: x == 'True',
        choices=[(True, 'Yes'), (False, 'No')],
    )
