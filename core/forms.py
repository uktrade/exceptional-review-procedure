import json

from directory_components import forms
from directory_constants import choices
from directory_forms_api_client.forms import GovNotifyEmailActionMixin

from django.forms import Textarea, HiddenInput
from django.utils.safestring import mark_safe

from core import constants, fields

OTHER = 'OTHER'
TERMS_LABEL = mark_safe('I accept the <a href="#" target="_blank">terms and conditions</a> of the gov.uk service.')
INDUSTRY_CHOICES = [('', 'Please select')] + choices.SECTORS + [('OTHER', 'Other')]
INCOME_BRACKET_CHOICES = (
    ('', 'Please select'),
    ("0-11.85k", "Up to £11,850"),
    ("11.85k-46.35k", "£11,851 to £46,350"),
    ("46.35k-150k", "£46,351 to £150,000"),
    ("150k+", "Over £150,000")
)
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
HELP_TEXT_SELECT_CHANGE_TYPE = 'Select actual, expected, or both'


class ConsumerChoiceChangeForm(forms.Form):
    choice_change_type = forms.MultipleChoiceField(
        label='',
        help_text=HELP_TEXT_SELECT_CHANGE_TYPE,
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
        help_text=HELP_TEXT_SELECT_CHANGE_TYPE,
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
        help_text=HELP_TEXT_SELECT_CHANGE_TYPE,
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
        help_text=HELP_TEXT_SELECT_CHANGE_TYPE,
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
        help_text=HELP_TEXT_SELECT_CHANGE_TYPE,
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
        help_text=HELP_TEXT_SELECT_CHANGE_TYPE,
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
        help_text="To feedback on other types of goods, you'll need to submit another form afterwards.",
        required=False,
        container_css_classes='form-group text-input-with-submit-button-container',
        widget=fields.TextInputWithSubmitButton(attrs={'form': 'search-form'}),
    )
    commodity = forms.CharField(
        label='Commodity codes',
        help_text='Find the commodity codes via the commodity code browser.',
        widget=HiddenInput,
    )

    def clean(self):
        super().clean()
        if not self.cleaned_data.get('commodity'):
            self.add_error('term', self.MESSAGE_MISSING_PRODUCT)

    def clean_commodity(self):
        return json.loads(self.cleaned_data['commodity'])


class OtherMetricNameForm(forms.Form):
    other_metric_name = forms.CharField(label='Metric name')


Q3_2019_LABEL = 'July to September 2019'
Q2_2019_LABEL = 'April to June 2019'
Q1_2019_LABEL = 'January to March 2019'
Q4_2018_label = 'October to December 2018'


class SalesVolumeBeforeBrexitForm(fields.BindNestedFormMixin, forms.Form):
    sales_volume_unit = fields.RadioNested(
        label='Select a metric',
        choices=SALES_VOLUME_UNIT_CHOICES,
        nested_form_class=OtherMetricNameForm,
        nested_form_choice=OTHER,
    )
    quarter_three_2019_sales_volume = forms.IntegerField(
        label=Q3_2019_LABEL
    )
    quarter_two_2019_sales_volume = forms.IntegerField(
        label=Q2_2019_LABEL
    )
    quarter_one_2019_sales_volume = forms.IntegerField(
        label=Q1_2019_LABEL
    )
    quarter_four_2018_sales_volume = forms.IntegerField(
        label=Q4_2018_label
    )


class SalesRevenueBeforeBrexitForm(forms.Form):
    quarter_three_2019_sales_revenue = forms.IntegerField(
        label=Q3_2019_LABEL,
        container_css_classes='form-group prefix-pound',
    )
    quarter_two_2019_sales_revenue = forms.IntegerField(
        label=Q2_2019_LABEL,
        container_css_classes='form-group prefix-pound',
    )
    quarter_one_2019_sales_revenue = forms.IntegerField(
        label=Q1_2019_LABEL,
        container_css_classes='form-group prefix-pound',
    )
    quarter_four_2018_sales_revenue = forms.IntegerField(
        label=Q4_2018_label,
        container_css_classes='form-group prefix-pound',
    )


class SalesAfterBrexitForm(fields.BindNestedFormMixin, forms.Form):
    has_volume_changed = fields.RadioNested(
        label='Import volumes',
        nested_form_class=VolumeChangeForm,
        coerce=lambda x: x == 'True',
        choices=[
            (True, "I'm aware of changes to my import volumes for these goods"),
            (False, "I'm not aware of changes to my import volumes for these goods")
        ],
    )
    has_price_changed = fields.RadioNested(
        label='Sales prices',
        nested_form_class=PriceChangeForm,
        coerce=lambda x: x == 'True',
        choices=[
            (True, "I'm aware of changes to my prices for products related to these goods"),
            (False, "I'm not aware of changes to my prices for products related to these goods")
        ],
    )


class ExportsAfterBrexitForm(fields.BindNestedFormMixin, forms.Form):
    has_volume_changed = fields.RadioNested(
        label='Export volumes',
        nested_form_class=VolumeChangeForm,
        coerce=lambda x: x == 'True',
        choices=[
            (True, "I'm aware of changes to my UK export volumes for these goods"),
            (False, "I'm not aware of changes to my import volumes for these goods")
        ],
    )
    has_price_changed = fields.RadioNested(
        label='Prices changes',
        nested_form_class=PriceChangeForm,
        coerce=lambda x: x == 'True',
        choices=[
            (True, "I'm aware of changes to my UK export prices for these goods"),
            (False, "I'm not aware of changes to my UK export prices for these goods")
        ],
    )


class MarketSizeAfterBrexitForm(fields.BindNestedFormMixin, forms.Form):
    has_market_size_changed = fields.RadioNested(
        label='Sales volume',
        nested_form_class=MarketSizeChangeForm,
        coerce=lambda x: x == 'True',
        choices=[
            (True, "I'm aware of changes to my sales volumes for these goods"),
            (False, "I'm not aware of changes to my sales volumes for these goods")
        ],
    )
    has_market_price_changed = fields.RadioNested(
        label='Sales price',
        nested_form_class=MarketPriceChangeForm,
        coerce=lambda x: x == 'True',
        choices=[
            (True, "I'm aware of changes to my prices for these imported goods"),
            (False, "I'm not aware of changes to my prices for these imported goods")
        ],
    )


class ExportMarketSizeAfterBrexitForm(fields.BindNestedFormMixin, forms.Form):
    has_market_size_changed = fields.RadioNested(
        label='Sales volume',
        nested_form_class=MarketSizeChangeForm,
        coerce=lambda x: x == 'True',
        choices=[
            (True, "I'm aware of changes in volume for others exporting these goods to the UK"),
            (False, "I'm not aware of changes in volume for others exporting these goods to the UK")
        ],
    )
    has_market_price_changed = fields.RadioNested(
        label='Sales price',
        nested_form_class=MarketPriceChangeForm,
        coerce=lambda x: x == 'True',
        choices=[
            (
                True,
                "I'm aware of changes to the prices others are selling these goods for when exporting to the UK"
            ),
            (
                False,
                "I'm not aware of changes to the prices others are selling these goods for when exporting to the UK"
            )
        ],
    )


class OtherChangesAfterBrexitForm(fields.BindNestedFormMixin, forms.Form):
    has_other_changes = fields.RadioNested(
        label='',
        nested_form_class=OtherChangesForm,
        coerce=lambda x: x == 'True',
        choices=[
            (True, "I'm aware of other changes to my business"),
            (False, "I'm not aware of other changes to my business"),
        ],
    )
    other_information = forms.CharField(
        label='Other information',
        help_text=(
            'Use this opportunity to give us any other supporting information.'
            ' Do not include any sensetive information.'
        ),
        widget=Textarea(attrs={'rows': 6}),
        required=False,
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


class ConsumerTypeForm(forms.Form):
    consumer_type = forms.ChoiceField(
        label='',
        choices=(
            (constants.CONSUMER_GROUP, 'Consumer group'),
            (constants.INDIVIDUAL_CONSUMER, 'Individual consumer'),
        ),
        widget=forms.RadioSelect(),
    )


class OutcomeForm(fields.BindNestedFormMixin, forms.Form):
    tariff_rate = forms.ChoiceField(
        label='Tariff rate change',
        choices=[
            (constants.INCREASE, 'I want the tariff rate increased'),
            (constants.DECREASE, 'I want the tariff rate decreased'),
            ('N/A', 'I want neither'),
        ],
        widget=forms.RadioSelect(),
    )
    tariff_quota = forms.ChoiceField(
        label='Tariff quota change',
        choices=[
            (constants.INCREASE, 'I want the tariff quota increased '),
            (constants.DECREASE, 'I want the tariff quota decreased'),
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
        choices=(('', 'Please select'),) + choices.EMPLOYEES,
        required=False,
    )
    turnover = forms.ChoiceField(
        label='Annual turnover for 2018-19',
        choices=TURNOVER_CHOICES,
        required=False,
    )
    employment_regions = fields.MultipleChoiceAutocomplateField(
        label='Where do you employ the most people?',
        choices=choices.EXPERTISE_REGION_CHOICES,
    )


class PersonalDetailsForm(forms.Form):
    given_name = forms.CharField(label='Given name',)
    family_name = forms.CharField(label='Family name')
    email = forms.EmailField(label='Email address')


class ConsumerPersonalDetailsForm(forms.Form):
    given_name = forms.CharField(label='Given name',)
    family_name = forms.CharField(label='Family name')
    email = forms.EmailField(label='Email address')
    income_bracket = forms.ChoiceField(
        label='Personal income before tax (optional)',
        required=False,
        choices=INCOME_BRACKET_CHOICES
    )
    consumer_region = forms.ChoiceField(
        label='Where do you live (optional)?',
        choices=[('', 'Please select')] + choices.EXPERTISE_REGION_CHOICES,
        required=False,
    )


class SummaryForm(forms.Form):
    captcha = fields.ReCaptchaField(
        label='',
        label_suffix='',
        container_css_classes='govuk-!-margin-top-6 govuk-!-margin-bottom-6',
    )
    terms_agreed = forms.BooleanField(label=TERMS_LABEL)


class SaveForLaterForm(GovNotifyEmailActionMixin, forms.Form):
    email = forms.EmailField(label='Email address')
    url = forms.CharField(widget=HiddenInput(), disabled=True)
    expiry_timestamp = forms.CharField(widget=HiddenInput(), disabled=True)


class ConsumerChangeForm(fields.BindNestedFormMixin, forms.Form):
    has_consumer_price_changed = fields.RadioNested(
        label='Sales changes',
        nested_form_class=PriceChangeForm,
        coerce=lambda x: x == 'True',
        choices=[
            (True, "I'm aware of price changes for these goods"),
            (False, "I'm not aware of price changes for these goods"),
        ],
    )
    has_consumer_choice_changed = fields.RadioNested(
        label='Choice changes',
        nested_form_class=ConsumerChoiceChangeForm,
        coerce=lambda x: x == 'True',
        choices=[
            (True, "I'm aware of changes to consumer choice for these goods"),
            (False, "I'm not aware of changes to consumer choice for these goods"),
        ],
    )


class ConsumerGroupForm(forms.Form):
    given_name = forms.CharField(label='Given name',)
    family_name = forms.CharField(label='Family name')
    email = forms.EmailField(label='Email address')
    organisation_name = forms.CharField(
        label='Organisation name',
    )
    consumer_regions = fields.MultipleChoiceAutocomplateField(
        label='Where are most of your consumers based?',
        choices=choices.EXPERTISE_REGION_CHOICES,
        required=False,
    )


class DevelopingCountryForm(forms.Form):
    country = forms.ChoiceField(
        choices=[('', 'Please select')] + [
            (item, item) for item in constants.GENERALISED_SYSTEM_OF_PERFERENCE_COUNTRIES
        ],
    )


class BusinessDetailsDevelopingCountryForm(forms.Form):
    company_name = forms.CharField(label='Company name')
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
        label='Annual turnover for 2018-19',
        choices=TURNOVER_CHOICES,
        required=False,
    )


class ImportedProductsUsageDetailsForm(forms.Form):
    imported_good_sector = forms.ChoiceField(
        label='Industry of product or service',
        choices=[('', 'Please select')] + choices.SECTORS,
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
    production_cost_percentage = forms.IntegerField(
        label='Percentage of total production costs',
        container_css_classes='form-group suffix-percentage',
    )


class CountriesImportSourceForm(forms.Form):
    import_countries = fields.MultipleChoiceAutocomplateField(
        label='',
        choices=[item for item in choices.COUNTRIES_AND_TERRITORIES if item[0] != 'GB'],
    )


class EquivalendUKGoodsDetailsForm(forms.Form):
    equivalent_uk_goods_details = forms.CharField(
        label="Tell us more ",
        help_text=(
            'Use this opportunity to give us any other supporting information.'
            'Do not include any sensetive information.'
        ),
        widget=Textarea(attrs={'rows': 6}),
    )


class EquivalendUKGoodsForm(fields.BindNestedFormMixin, forms.Form):
    equivalent_uk_goods = fields.RadioNested(
        label='',
        nested_form_class=EquivalendUKGoodsDetailsForm,
        coerce=lambda x: x == 'True',
        choices=[(True, 'Yes'), (False, 'No')],
    )


class NoOperationForm(forms.Form):
    pass
