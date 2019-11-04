import json
from unittest import mock

from directory_constants import choices
from directory_forms_api_client import actions
from directory_forms_api_client.helpers import Sender
from freezegun import freeze_time
import pytest
import requests

from django.core.cache import cache
from django.urls import reverse
from django.conf import settings

from core import constants, forms, helpers, views
from core.tests.helpers import build_wizard_data_shape, create_response, submit_step_factory, reload_urlconf


@pytest.fixture
def submit_step_routing(client):
    return submit_step_factory(client=client, url_name='user-type-routing')


@pytest.fixture
def submit_step_business(client):
    return submit_step_factory(client=client, url_name='wizard-business')


@pytest.fixture
def submit_step_consumer(client):
    return submit_step_factory(client=client, url_name='wizard-consumer')


@pytest.fixture
def submit_step_develping(client):
    return submit_step_factory(client=client, url_name='wizard-developing')


@pytest.fixture
def submit_step_importer(client):
    return submit_step_factory(client=client, url_name='wizard-importer')


@pytest.fixture(autouse=True)
def clear_cache():
    cache.clear()


@pytest.fixture(autouse=True)
def mock_search_commodity_by_term():
    response = create_response({
        'results': [{'description': 'Example', 'commodity_code': '1234'}],
        'total_results': 3,
    })
    patch = mock.patch.object(helpers, 'search_commodity_by_term', return_value=response)
    yield patch.start()
    patch.stop()


@pytest.fixture(autouse=True)
def mock_search_commodity_by_code():
    response = create_response({
        'results': [{'description': 'Example', 'commodity_code': '1700000000'}],
    })
    patch = mock.patch.object(helpers, 'search_commodity_by_code', return_value=response)
    yield patch.start()
    patch.stop()


@pytest.fixture
def steps_data_common(captcha_stub):
    return {
        constants.STEP_PRODUCT: {
            'commodity': json.dumps({'commodity_code': ['010130', '00', '00'], 'label': 'Asses'})
        },
        constants.STEP_SALES_VOLUME_BEFORE_BREXIT: {
            'sales_volume_unit': 'UNITS',
            'quarter_three_2019_sales_volume': 32019,
            'quarter_two_2019_sales_volume': 22019,
            'quarter_one_2019_sales_volume': 12019,
            'quarter_four_2018_sales_volume': 42018,
        },
        constants.STEP_PRODUCT_DETAIL: {},
        constants.STEP_SALES_REVENUE_BEFORE_BREXIT: {
            'quarter_three_2019_sales_revenue': 32019,
            'quarter_two_2019_sales_revenue': 22019,
            'quarter_one_2019_sales_revenue': 12019,
            'quarter_four_2018_sales_revenue': 42018,
        },
        constants.STEP_SALES_AFTER_BREXIT: {
            'has_volume_changed': False,
            'has_price_changed': False,
        },
        constants.STEP_MARKET_SIZE_AFTER_BREXIT: {
            'has_market_size_changed': False,
            'has_market_price_changed': False,
        },
        constants.STEP_OTHER_CHANGES: {
            'has_other_changes': False,
            'other_information': 'Foo Bar',
        },
        constants.STEP_MARKET_SIZE: {
            'market_size_known': True,
            'market_size_year': '2019',
            'market_size': 121232,
        },
        constants.STEP_OUTCOME: {
            'tariff_rate': constants.DECREASE,
            'tariff_quota': constants.DECREASE,
        },
        constants.STEP_SUMMARY: {
            'terms_agreed': True,
            'g-recaptcha-response': captcha_stub,
        }
    }


@pytest.fixture
def steps_data_business(steps_data_common):
    return {
        **steps_data_common,
        constants.STEP_BUSINESS: {
            'company_type': 'LIMITED',
            'company_name': 'Jim Ham',
            'company_number': '1234567',
            'sector': forms.INDUSTRY_CHOICES[1][0],
            'employees': choices.EMPLOYEES[1][0],
            'turnover': forms.TURNOVER_CHOICES[1][0],
            'employment_regions': choices.EXPERTISE_REGION_CHOICES[0][0]
        },
        constants.STEP_PERSONAL: {
            'given_name': 'Jim',
            'family_name': 'Example',
            'email': 'jim@example.com',
        },
    }


@pytest.fixture
def steps_data_consumer(steps_data_common):
    return {
        **steps_data_common,
        constants.STEP_CONSUMER_CHANGE: {
            'has_consumer_price_changed': True,
            'has_consumer_choice_changed': False,
            'price_changed_type': constants.ACTUAL,
            'price_change_comment': 'bar',
        },
        constants.STEP_PERSONAL: {
            'given_name': 'Jim',
            'family_name': 'Example',
            'email': 'jim@example.com',
            'income_bracket': forms.INCOME_BRACKET_CHOICES[1][0],
        },
        constants.STEP_CONSUMER_TYPE: {
            'consumer_type': constants.CONSUMER_GROUP,
        },
        constants.STEP_OTHER_CHANGES: {
            'other_information': 'Foo Bar',
        },
        constants.STEP_CONSUMER_GROUP: {
            'given_name': 'Jim',
            'family_name': 'Example',
            'email': 'jim@example.com',
            'organisation_name': 'Example corp',
            'consumer_regions': choices.EXPERTISE_REGION_CHOICES[0][0],
        },
    }


@pytest.fixture
def steps_data_developing(steps_data_common):
    return {
        **steps_data_common,
        constants.STEP_COUNTRY: {
            'country': constants.GENERALISED_SYSTEM_OF_PERFERENCE_COUNTRIES[0]
        },
        constants.STEP_BUSINESS: {
            'company_type': 'LIMITED',
            'company_name': 'Jim Ham',
            'company_number': '1234567',
            'sector': forms.INDUSTRY_CHOICES[1][0],
            'employees': choices.EMPLOYEES[1][0],
            'turnover': forms.TURNOVER_CHOICES[1][0],
            'employment_regions': choices.EXPERTISE_REGION_CHOICES[0][0]
        },
        constants.STEP_PERSONAL: {
            'given_name': 'Jim',
            'family_name': 'Example',
            'email': 'jim@example.com',
        },
    }


@pytest.fixture
def steps_data_importer(steps_data_common):
    return {
        **steps_data_common,
        constants.STEP_IMPORTED_PRODUCTS_USAGE: {
            'imported_goods_makes_something_else': False,
        },
        constants.STEP_PRODUCTION_PERCENTAGE: {
            'production_cost_percentage': 23,
        },
        constants.STEP_COUNTRIES_OF_IMPORT: {
            'import_countries': ['FR'],
        },
        constants.STEP_EQUIVALANT_UK_GOODS: {
            'equivalent_uk_goods': 'False',
        },
        constants.STEP_BUSINESS: {
            'company_type': 'LIMITED',
            'company_name': 'Jim Ham',
            'company_number': '1234567',
            'sector': forms.INDUSTRY_CHOICES[1][0],
            'employees': choices.EMPLOYEES[1][0],
            'turnover': forms.TURNOVER_CHOICES[1][0],
            'employment_regions': choices.EXPERTISE_REGION_CHOICES[0][0]
        },
        constants.STEP_PERSONAL: {
            'given_name': 'Jim',
            'family_name': 'Example',
            'email': 'jim@example.com',
        },
    }


def test_privacy_policy(client):
    url = reverse('privacy-policy')
    response = client.get(url)

    assert response.status_code == 200
    assert response.template_name == [views.PrivacyPolicyView.template_name]


def test_cookies(client):
    url = reverse('cookies')
    response = client.get(url)

    assert response.status_code == 200
    assert response.template_name == [views.CookiesView.template_name]


def test_landing_page(client):

    url = reverse('landing-page')
    response = client.get(url)

    assert response.status_code == 200
    assert response.template_name == 'core/landing-page.html'


def test_landing_page_service_holding(client, settings):

    settings.FEATURE_FLAGS['SERVICE_HOLDING_PAGE_ON'] = True

    url = reverse('landing-page')
    response = client.get(url)

    assert response.status_code == 200
    assert response.template_name == 'core/service-holding-page.html'
    assert response.context_data['service_availability_start_date'] == settings.SERVICE_AVAILABILITY_START_DATE
    assert response.context_data['service_availability_end_date'] == settings.SERVICE_AVAILABILITY_END_DATE

    settings.FEATURE_FLAGS['SERVICE_HOLDING_PAGE_ON'] = False


def test_companies_house_search_no_term(client):
    url = reverse('companies-house-search')
    response = client.get(url)

    assert response.status_code == 400


@mock.patch('core.views.ch_search_api_client.company.search_companies')
def test_companies_house_search_api_error(mock_search, client, settings):
    mock_search.return_value = create_response(status_code=400)
    url = reverse('companies-house-search')

    with pytest.raises(requests.HTTPError):
        client.get(url, data={'term': 'thing'})


@mock.patch('core.views.ch_search_api_client.company.search_companies')
def test_companies_house_search_api_success(mock_search, client, settings):

    mock_search.return_value = create_response({'items': [{'name': 'Smashing corp'}]})
    url = reverse('companies-house-search')

    response = client.get(url, data={'term': 'thing'})

    assert response.status_code == 200
    assert response.content == b'[{"name":"Smashing corp"}]'


@mock.patch.object(helpers, 'search_hierarchy')
def test_business_search_term(
    mock_search_hierarchy, client, mock_search_commodity_by_term
):
    mock_search_hierarchy.return_value = create_response({'results': [{'key': 'foo'}]})

    url = reverse('wizard-business', kwargs={'step': constants.STEP_PRODUCT})
    response = client.get(url, {'product-search-term': 'foo'})
    assert response.status_code == 200
    assert response.context_data['search'] == {
        'results': [{'description': 'Example', 'commodity_code': '1234'}],
        'total_results': 3
    }
    assert response.context_data['term'] == 'foo'
    assert response.context['pagination_url'] == (
        reverse('wizard-business', kwargs={'step': constants.STEP_PRODUCT}) + '?product-search-term=foo'
    )
    assert 'paginator_page' in response.context_data
    assert mock_search_commodity_by_term.call_count == 1
    assert mock_search_commodity_by_term.call_args == mock.call(term='foo', page=1)


@mock.patch.object(helpers, 'search_hierarchy')
def test_business_search_code(mock_search_hierarchy, client, mock_search_commodity_by_code):
    mock_search_hierarchy.return_value = create_response({'results': [{'key': 'foo'}]})

    url = reverse('wizard-business', kwargs={'step': constants.STEP_PRODUCT})
    response = client.get(url, {'product-search-term': '17'})
    assert response.status_code == 200
    assert response.context_data['search'] == {
        'results': [{'description': 'Example', 'commodity_code': '1700000000'}],
    }
    assert response.context_data['term'] == '17'
    assert 'pagination_url' not in response.context
    assert 'pagination_page' not in response.context_data
    assert mock_search_commodity_by_code.call_count == 1
    assert mock_search_commodity_by_code.call_args == mock.call(code='17')


def test_skip_to_summary(steps_data_business, client):
    step = constants.STEP_SALES_VOLUME_BEFORE_BREXIT
    url = reverse('wizard-business', kwargs={'step': step})
    data = build_wizard_data_shape(
        data=steps_data_business[step],
        prefix=views.BusinessWizard().get_prefix(None),
        step_name=step,
    )

    response = client.post(f'{url}?change=True', data)

    assert response.status_code == 302
    assert response.url == reverse('wizard-business', kwargs={'step': constants.STEP_SUMMARY})


@mock.patch.object(helpers, 'search_hierarchy')
def test_business_search_code_space(mock_search_hierarchy, client, mock_search_commodity_by_code):
    mock_search_hierarchy.return_value = create_response({'results': [{'key': 'foo'}]})

    url = reverse('wizard-business', kwargs={'step': constants.STEP_PRODUCT})
    response = client.get(url, {'product-search-term': '1700 00 00'})
    assert response.status_code == 200
    assert response.context_data['search'] == {
        'results': [{'description': 'Example', 'commodity_code': '1700000000'}],
    }
    assert response.context_data['term'] == '17000000'
    assert 'pagination_url' not in response.context
    assert 'pagination_page' not in response.context_data
    assert mock_search_commodity_by_code.call_count == 1
    assert mock_search_commodity_by_code.call_args == mock.call(code='17000000')


@mock.patch.object(helpers, 'search_hierarchy')
@mock.patch('captcha.fields.ReCaptchaField.clean', mock.Mock)
@mock.patch.object(actions, 'ZendeskAction')
def test_business_end_to_end(
    mock_zendesk_action, mock_search_hierarchy, submit_step_business, captcha_stub, client, steps_data_business
):
    hierarchy = [{'key': 'foo'}]
    mock_search_hierarchy.return_value = create_response({'results': hierarchy})

    # PRODUCT
    response = client.get(reverse('wizard-business', kwargs={'step': constants.STEP_PRODUCT}))
    assert response.status_code == 200
    assert response.context_data['hierarchy'] == hierarchy
    response = submit_step_business(steps_data_business[constants.STEP_PRODUCT])
    assert response.status_code == 302

    # PRODUCT_DETAIL
    response = client.get(response.url)
    assert response.status_code == 200
    response = submit_step_business(steps_data_business[constants.STEP_PRODUCT_DETAIL])
    assert response.status_code == 302

    # SALES_VOLUME_BEFORE_BREXIT
    response = client.get(response.url)
    assert response.status_code == 200
    response = submit_step_business(steps_data_business[constants.STEP_SALES_VOLUME_BEFORE_BREXIT])
    assert response.status_code == 302

    # SALES_REVENUE_BEFORE_BREXIT
    response = client.get(response.url)
    assert response.status_code == 200
    response = submit_step_business(steps_data_business[constants.STEP_SALES_REVENUE_BEFORE_BREXIT])
    assert response.status_code == 302

    # SALES_AFTER_BREXIT
    response = client.get(response.url)
    assert response.status_code == 200
    response = submit_step_business(steps_data_business[constants.STEP_SALES_AFTER_BREXIT])
    assert response.status_code == 302

    # MARKET_SIZE_AFTER_BREXIT
    response = client.get(response.url)
    assert response.status_code == 200
    response = submit_step_business(steps_data_business[constants.STEP_MARKET_SIZE_AFTER_BREXIT])
    assert response.status_code == 302

    # OTHER_CHANGES
    response = client.get(response.url)
    assert response.status_code == 200
    response = submit_step_business(steps_data_business[constants.STEP_OTHER_CHANGES])
    assert response.status_code == 302

    # MARKET_SIZE
    response = client.get(response.url)
    assert response.status_code == 200
    response = submit_step_business(steps_data_business[constants.STEP_MARKET_SIZE])
    assert response.status_code == 302

    # OUTCOME
    response = client.get(response.url)
    assert response.status_code == 200
    response = submit_step_business(steps_data_business[constants.STEP_OUTCOME])
    assert response.status_code == 302

    # BUSINESS
    response = client.get(response.url)
    assert response.status_code == 200
    response = submit_step_business(steps_data_business[constants.STEP_BUSINESS])
    assert response.status_code == 302

    # PERSONAL
    response = client.get(response.url)
    assert response.status_code == 200
    response = submit_step_business(steps_data_business[constants.STEP_PERSONAL])
    assert response.status_code == 302
    # SUMMARY
    response = client.get(response.url)
    assert response.status_code == 200
    assert response.context_data['summary'] == {
        'captcha': '-',
        'commodity': {'commodity_code': ['010130', '00', '00'], 'label': 'Asses'},
        'company_name': 'Jim Ham',
        'company_number': '1234567',
        'company_type': 'UK private or public limited company',
        'email': 'jim@example.com',
        'employees': '11-50',
        'employment_regions': ['North East'],
        'family_name': 'Example',
        'given_name': 'Jim',
        'has_market_price_changed': "I'm not aware of changes to my prices for these imported goods",
        'has_market_size_changed': "I'm not aware of changes to my sales volumes for these goods",
        'has_other_changes': "I'm not aware of other changes to my business",
        'has_other_changes_type': [],
        'has_price_changed': "I'm not aware of changes to my prices for products related to these goods",
        'has_volume_changed': "I'm not aware of changes to my import volumes for these goods",
        'market_price_change_comment': '',
        'market_price_changed_type': [],
        'market_size': 121232,
        'market_size_change_comment': '',
        'market_size_changed_type': [],
        'market_size_known': 'Yes',
        'market_size_year': '2019',
        'other_changes_comment': '',
        'other_information': 'Foo Bar',
        'other_metric_name': '',
        'price_change_comment': '',
        'price_changed_type': [],
        'quarter_four_2018_sales_revenue': 42018,
        'quarter_four_2018_sales_volume': 42018,
        'quarter_one_2019_sales_revenue': 12019,
        'quarter_one_2019_sales_volume': 12019,
        'quarter_three_2019_sales_revenue': 32019,
        'quarter_three_2019_sales_volume': 32019,
        'quarter_two_2019_sales_revenue': 22019,
        'quarter_two_2019_sales_volume': 22019,
        'sales_volume_unit': 'units (number of items)',
        'sector': 'Advanced Engineering',
        'tariff_quota': 'I want the tariff quota decreased',
        'tariff_rate': 'I want the tariff rate decreased',
        'term': '',
        'terms_agreed': '-',
        'turnover': 'under £25,000',
        'volume_changed_type': [],
        'volumes_change_comment': '',
    }

    response = submit_step_business(steps_data_business[constants.STEP_SUMMARY])
    assert response.status_code == 302
    # FINISH
    response = client.get(response.url, REMOTE_ADDR='192.168.93.2')

    assert response.status_code == 200
    assert mock_zendesk_action.call_count == 1
    assert mock_zendesk_action.call_args == mock.call(
        subject='ERP form was submitted',
        full_name='Jim Example',
        service_name=constants.ZENDESK_SERVICE_NAME,
        subdomain=settings.ERP_ZENDESK_SUBDOMAIN,
        email_address='jim@example.com',
        form_url=reverse('wizard-business', kwargs={'step': constants.STEP_SUMMARY}),
        form_session=mock.ANY,
        sender=Sender(
            email_address='jim@example.com',
            country_code=None,
            ip_address='192.168.93.2',
        ),
    )
    assert mock_zendesk_action().save.call_count == 1
    assert mock_zendesk_action().save.call_args == mock.call({
        'commodity': {'commodity_code': ['010130', '00', '00'], 'label': 'Asses'},
        'company_name': 'Jim Ham',
        'company_number': '1234567',
        'company_type': 'LIMITED',
        'email': 'jim@example.com',
        'employees': '11-50',
        'employment_regions': ['NORTH_EAST'],
        'family_name': 'Example',
        'given_name': 'Jim',
        'has_market_price_changed': False,
        'has_market_size_changed': False,
        'has_other_changes': False,
        'has_price_changed': False,
        'has_volume_changed': False,
        'market_size_known': True,
        'other_information': 'Foo Bar',
        'quarter_four_2018_sales_revenue': 42018,
        'quarter_four_2018_sales_volume': 42018,
        'quarter_one_2019_sales_revenue': 12019,
        'quarter_one_2019_sales_volume': 12019,
        'quarter_three_2019_sales_revenue': 32019,
        'quarter_three_2019_sales_volume': 32019,
        'quarter_two_2019_sales_revenue': 22019,
        'quarter_two_2019_sales_volume': 22019,
        'sales_volume_unit': 'UNITS',
        'sector': 'SL10001',
        'tariff_quota': 'DECREASE',
        'tariff_rate': 'DECREASE',
        'turnover': '0-25k',
    })

    # checking details are remembered even after submitting the form
    steps = [
        constants.STEP_PRODUCT,
        constants.STEP_PRODUCT_DETAIL,
        constants.STEP_SALES_VOLUME_BEFORE_BREXIT,
        constants.STEP_SALES_REVENUE_BEFORE_BREXIT,
        constants.STEP_SALES_AFTER_BREXIT,
        constants.STEP_MARKET_SIZE_AFTER_BREXIT,
        constants.STEP_OTHER_CHANGES,
        constants.STEP_MARKET_SIZE,
        constants.STEP_OUTCOME,
    ]
    for step in steps:
        response = client.get(reverse('wizard-business', kwargs={'step': step}))
        assert response.status_code == 200
        assert response.context_data['form'].data == {}

    # BUSINESS
    response = client.get(reverse('wizard-business', kwargs={'step': constants.STEP_BUSINESS}))
    assert response.status_code == 200
    assert response.context_data['form'].cleaned_data == {
        'company_type': 'LIMITED',
        'company_name': 'Jim Ham',
        'company_number': '1234567',
        'sector': 'SL10001',
        'employees': '11-50',
        'turnover': '0-25k',
        'employment_regions': ['NORTH_EAST']
    }

    # PERSONAL
    response = client.get(reverse('wizard-business', kwargs={'step': constants.STEP_PERSONAL}))
    assert response.status_code == 200
    assert response.context_data['form'].cleaned_data == {
        'given_name': 'Jim',
        'family_name': 'Example',
        'email': 'jim@example.com',
    }


@mock.patch.object(helpers, 'search_hierarchy')
@mock.patch('captcha.fields.ReCaptchaField.clean', mock.Mock)
@mock.patch.object(actions, 'ZendeskAction')
def test_consumer_end_to_end(
    mock_zendesk_action, mock_search_hierarchy, submit_step_consumer, captcha_stub, client, steps_data_consumer
):
    hierarchy = [{'key': 'foo'}]
    mock_search_hierarchy.return_value = create_response({'results': hierarchy})

    # PRODUCT
    response = client.get(reverse('wizard-consumer', kwargs={'step': constants.STEP_PRODUCT}))
    assert response.status_code == 200
    assert response.context_data['hierarchy'] == hierarchy
    response = submit_step_consumer(steps_data_consumer[constants.STEP_PRODUCT])
    assert response.status_code == 302

    # PRODUCT_DETAIL
    response = client.get(response.url)
    assert response.status_code == 200
    response = submit_step_consumer(steps_data_consumer[constants.STEP_PRODUCT_DETAIL])
    assert response.status_code == 302

    # CONSUMER_CHANGE
    response = client.get(response.url)
    assert response.status_code == 200
    response = submit_step_consumer(steps_data_consumer[constants.STEP_CONSUMER_CHANGE])
    assert response.status_code == 302

    # OTHER_CHANGES
    response = client.get(response.url)
    assert response.status_code == 200
    response = submit_step_consumer(steps_data_consumer[constants.STEP_OTHER_CHANGES])
    assert response.status_code == 302

    # CONSUMER_TYPE
    response = client.get(response.url)
    assert response.status_code == 200
    response = submit_step_consumer(steps_data_consumer[constants.STEP_CONSUMER_TYPE])
    assert response.status_code == 302

    # CONSUMER_GROUP
    response = client.get(response.url)
    assert response.status_code == 200
    response = submit_step_consumer(
        data=steps_data_consumer[constants.STEP_CONSUMER_GROUP],
        step_name=constants.STEP_CONSUMER_GROUP,
    )
    assert response.status_code == 302

    # SUMMARY
    response = client.get(response.url)
    assert response.status_code == 200
    assert response.context_data['summary'] == {
        'captcha': '-',
        'choice_change_type': [], 'choice_change_comment': '',
        'commodity': {'commodity_code': ['010130', '00', '00'], 'label': 'Asses'},
        'consumer_regions': ['North East'],
        'consumer_type': 'Consumer group',
        'email': 'jim@example.com',
        'family_name': 'Example',
        'given_name': 'Jim',
        'has_consumer_price_changed': "I'm aware of price changes for these goods",
        'has_consumer_choice_changed': "I'm not aware of changes to consumer choice for these goods",
        'organisation_name': 'Example corp',
        'other_information': 'Foo Bar',
        'price_change_comment': 'bar',
        'price_changed_type': ['Actual change in price'],
        'term': '',
        'terms_agreed': '-',
    }

    response = submit_step_consumer(
        data=steps_data_consumer[constants.STEP_SUMMARY],
        step_name=constants.STEP_SUMMARY,
    )
    assert response.status_code == 302

    # FINISH
    response = client.get(response.url, REMOTE_ADDR='192.168.93.2')

    assert response.status_code == 200
    assert mock_zendesk_action.call_count == 1
    assert mock_zendesk_action.call_args == mock.call(
        subject='ERP form was submitted',
        full_name='Jim Example',
        service_name=constants.ZENDESK_SERVICE_NAME,
        subdomain=settings.ERP_ZENDESK_SUBDOMAIN,
        email_address='jim@example.com',
        form_url=reverse('wizard-consumer', kwargs={'step': constants.STEP_SUMMARY}),
        form_session=mock.ANY,
        sender=Sender(
            email_address='jim@example.com',
            country_code=None,
            ip_address='192.168.93.2',
        ),
    )
    assert mock_zendesk_action().save.call_count == 1
    assert mock_zendesk_action().save.call_args == mock.call({
        'commodity': {'commodity_code': ['010130', '00', '00'], 'label': 'Asses'},
        'consumer_regions': ['NORTH_EAST'],
        'consumer_type': 'CONSUMER_GROUP',
        'email': 'jim@example.com',
        'family_name': 'Example',
        'given_name': 'Jim',
        'has_consumer_choice_changed': False,
        'has_consumer_price_changed': True,
        'organisation_name': 'Example corp',
        'other_information': 'Foo Bar',
    })

    # checking details are remembered even after submitting the form
    steps = [
        constants.STEP_PRODUCT,
        constants.STEP_PRODUCT_DETAIL,
    ]
    for step in steps:
        response = client.get(reverse('wizard-consumer', kwargs={'step': step}))
        assert response.status_code == 200
        assert response.context_data['form'].data == {}

    # CONSUMER_GROUP
    response = client.get(reverse('wizard-consumer', kwargs={'step': constants.STEP_CONSUMER_GROUP}))
    assert response.status_code == 200
    assert response.context_data['form'].cleaned_data == {
        'consumer_regions': ['NORTH_EAST'],
        'email': 'jim@example.com',
        'family_name': 'Example',
        'given_name': 'Jim',
        'organisation_name': 'Example corp',
    }


@mock.patch.object(helpers, 'search_hierarchy')
@mock.patch('captcha.fields.ReCaptchaField.clean', mock.Mock)
@mock.patch.object(actions, 'ZendeskAction')
def test_developing_country_business_end_to_end(
    mock_zendesk_action, mock_search_hierarchy, submit_step_develping, captcha_stub, client, steps_data_developing
):
    hierarchy = [{'key': 'foo'}]
    mock_search_hierarchy.return_value = create_response({'results': hierarchy})

    # COUNTRY
    response = client.get(reverse('wizard-developing', kwargs={'step': constants.STEP_COUNTRY}))
    assert response.status_code == 200
    response = submit_step_develping(steps_data_developing[constants.STEP_COUNTRY])
    assert response.status_code == 302

    # PRODUCT
    response = client.get(response.url)
    assert response.status_code == 200
    assert response.context_data['hierarchy'] == hierarchy
    response = submit_step_develping(steps_data_developing[constants.STEP_PRODUCT])
    assert response.status_code == 302

    # PRODUCT_DETAIL
    response = client.get(response.url)
    assert response.status_code == 200
    response = submit_step_develping(steps_data_developing[constants.STEP_PRODUCT_DETAIL])
    assert response.status_code == 302

    # SALES_VOLUME_BEFORE_BREXIT
    response = client.get(response.url)
    assert response.status_code == 200
    response = submit_step_develping(steps_data_developing[constants.STEP_SALES_VOLUME_BEFORE_BREXIT])
    assert response.status_code == 302

    # SALES_REVENUE_BEFORE_BREXIT
    response = client.get(response.url)
    assert response.status_code == 200
    response = submit_step_develping(steps_data_developing[constants.STEP_SALES_REVENUE_BEFORE_BREXIT])
    assert response.status_code == 302

    # SALES_AFTER_BREXIT
    response = client.get(response.url)
    assert response.status_code == 200
    response = submit_step_develping(steps_data_developing[constants.STEP_SALES_AFTER_BREXIT])
    assert response.status_code == 302

    # MARKET_SIZE_AFTER_BREXIT
    response = client.get(response.url)
    assert response.status_code == 200
    response = submit_step_develping(steps_data_developing[constants.STEP_MARKET_SIZE_AFTER_BREXIT])
    assert response.status_code == 302

    # OTHER_CHANGES
    response = client.get(response.url)
    assert response.status_code == 200
    response = submit_step_develping(steps_data_developing[constants.STEP_OTHER_CHANGES])
    assert response.status_code == 302

    # OUTCOME
    response = client.get(response.url)
    assert response.status_code == 200
    response = submit_step_develping(steps_data_developing[constants.STEP_OUTCOME])
    assert response.status_code == 302

    # BUSINESS
    response = client.get(response.url)
    assert response.status_code == 200
    response = submit_step_develping(steps_data_developing[constants.STEP_BUSINESS])
    assert response.status_code == 302

    # PERSONAL
    response = client.get(response.url)
    assert response.status_code == 200
    response = submit_step_develping(steps_data_developing[constants.STEP_PERSONAL])
    assert response.status_code == 302

    # SUMMARY
    response = client.get(response.url)
    assert response.status_code == 200
    assert response.context_data['summary'] == {
        'country': 'Afghanistan',
        'term': '',
        'commodity': {'commodity_code': ['010130', '00', '00'], 'label': 'Asses'},
        'sales_volume_unit': 'units (number of items)',
        'quarter_three_2019_sales_volume': 32019,
        'quarter_two_2019_sales_volume': 22019,
        'quarter_one_2019_sales_volume': 12019,
        'quarter_four_2018_sales_volume': 42018,
        'other_metric_name': '',
        'quarter_three_2019_sales_revenue': 32019,
        'quarter_two_2019_sales_revenue': 22019,
        'quarter_one_2019_sales_revenue': 12019,
        'quarter_four_2018_sales_revenue': 42018,
        'has_volume_changed': "I'm not aware of changes to my import volumes for these goods",
        'has_price_changed': "I'm not aware of changes to my UK export prices for these goods",
        'volume_changed_type': [],
        'volumes_change_comment': '',
        'price_changed_type': [],
        'price_change_comment': '',
        'has_market_size_changed': "I'm not aware of changes in volume for others exporting these goods to the UK",
        'has_market_price_changed': (
            "I'm not aware of changes to the prices others are selling these goods for when exporting to the UK"
        ),
        'market_size_changed_type': [],
        'market_size_change_comment': '',
        'market_price_changed_type': [],
        'market_price_change_comment': '',
        'has_other_changes': "I'm not aware of other changes to my business",
        'other_information': 'Foo Bar',
        'has_other_changes_type': [],
        'other_changes_comment': '',
        'tariff_rate': 'I want the tariff rate decreased',
        'tariff_quota': 'I want the tariff quota decreased',
        'company_name': 'Jim Ham',
        'sector': 'Advanced Engineering',
        'employees': '11-50',
        'turnover': 'under £25,000',
        'given_name': 'Jim',
        'family_name': 'Example',
        'email': 'jim@example.com',
        'captcha': '-',
        'terms_agreed': '-',
    }

    response = submit_step_develping(steps_data_developing[constants.STEP_SUMMARY])
    assert response.status_code == 302

    # FINISH
    response = client.get(response.url)

    assert response.status_code == 200
    assert mock_zendesk_action.call_count == 1
    assert mock_zendesk_action.call_args == mock.call(
        subject='ERP form was submitted',
        full_name='Jim Example',
        service_name=constants.ZENDESK_SERVICE_NAME,
        subdomain=settings.ERP_ZENDESK_SUBDOMAIN,
        email_address='jim@example.com',
        form_url=reverse('wizard-developing', kwargs={'step': constants.STEP_SUMMARY}),
        form_session=mock.ANY,
        sender=Sender(
            email_address='jim@example.com',
            country_code=None,
            ip_address='127.0.0.1',
        ),
    )
    assert mock_zendesk_action().save.call_count == 1
    assert mock_zendesk_action().save.call_args == mock.call({
        'commodity': {'commodity_code': ['010130', '00', '00'], 'label': 'Asses'},
        'company_name': 'Jim Ham',
        'country': 'Afghanistan',
        'email': 'jim@example.com',
        'employees': '11-50',
        'family_name': 'Example',
        'given_name': 'Jim',
        'has_market_price_changed': False,
        'has_market_size_changed': False,
        'has_other_changes': False,
        'has_price_changed': False,
        'has_volume_changed': False,
        'other_information': 'Foo Bar',
        'quarter_four_2018_sales_revenue': 42018,
        'quarter_four_2018_sales_volume': 42018,
        'quarter_one_2019_sales_revenue': 12019,
        'quarter_one_2019_sales_volume': 12019,
        'quarter_three_2019_sales_revenue': 32019,
        'quarter_three_2019_sales_volume': 32019,
        'quarter_two_2019_sales_revenue': 22019,
        'quarter_two_2019_sales_volume': 22019,
        'sales_volume_unit': 'UNITS',
        'sector': 'SL10001',
        'tariff_quota': 'DECREASE',
        'tariff_rate': 'DECREASE',
        'turnover': '0-25k',
    })

    # checking details are remembered even after submitting the form
    steps = [
        constants.STEP_COUNTRY,
        constants.STEP_PRODUCT,
        constants.STEP_PRODUCT_DETAIL,
        constants.STEP_SALES_VOLUME_BEFORE_BREXIT,
        constants.STEP_SALES_REVENUE_BEFORE_BREXIT,
        constants.STEP_SALES_AFTER_BREXIT,
        constants.STEP_MARKET_SIZE_AFTER_BREXIT,
        constants.STEP_OTHER_CHANGES,
        constants.STEP_OUTCOME,
    ]
    for step in steps:
        response = client.get(reverse('wizard-developing', kwargs={'step': step}))
        assert response.status_code == 200
        assert response.context_data['form'].data == {}

    # BUSINESS
    response = client.get(reverse('wizard-developing', kwargs={'step': constants.STEP_BUSINESS}))
    assert response.status_code == 200
    assert response.context_data['form'].cleaned_data == {
        'company_name': 'Jim Ham',
        'sector': 'SL10001',
        'employees': '11-50',
        'turnover': '0-25k',
    }

    # PERSONAL
    response = client.get(reverse('wizard-developing', kwargs={'step': constants.STEP_PERSONAL}))
    assert response.status_code == 200
    assert response.context_data['form'].cleaned_data == {
        'given_name': 'Jim',
        'family_name': 'Example',
        'email': 'jim@example.com',
    }


@mock.patch.object(helpers, 'search_hierarchy')
def test_consumer_end_to_end_nested_validation_error(
    mock_search_hierarchy, submit_step_consumer, client, steps_data_consumer
):
    hierarchy = [{'key': 'foo'}]
    mock_search_hierarchy.return_value = create_response({'results': hierarchy})

    # PRODUCT
    response = client.get(reverse('wizard-business', kwargs={'step': constants.STEP_PRODUCT}))
    assert response.status_code == 200
    assert response.context_data['hierarchy'] == hierarchy
    response = submit_step_consumer(steps_data_consumer[constants.STEP_PRODUCT])
    assert response.status_code == 302

    # PRODUCT_DETAIL
    response = client.get(response.url)
    assert response.status_code == 200
    response = submit_step_consumer(steps_data_consumer[constants.STEP_PRODUCT_DETAIL])
    assert response.status_code == 302

    # CONSUMER_CHANGE
    response = client.get(response.url)
    assert response.status_code == 200
    response = submit_step_consumer({'has_consumer_price_changed': 'True', 'has__consumerchoice_changed': 'False'})
    assert response.status_code == 200
    field = response.context_data['form'].fields['has_consumer_price_changed']
    assert 'has_consumer_price_changed' in response.context_data['form'].errors
    assert 'price_changed_type' in field.nested_form.errors
    assert 'price_change_comment' in field.nested_form.errors


def test_wizard_save_for_later_suspious(client):
    url = reverse('wizard-business', kwargs={'step': constants.STEP_SALES_AFTER_BREXIT})
    response = client.post(url)

    assert response.status_code == 400


def test_wizard_save_for_later(submit_step_business, steps_data_business):
    expected_url = reverse("save-for-later")
    return_url = reverse('wizard-business', kwargs={'step': constants.STEP_SALES_AFTER_BREXIT})
    response = submit_step_business(steps_data_business[constants.STEP_PRODUCT])
    assert response.status_code == 302

    response = submit_step_business(steps_data_business[constants.STEP_PRODUCT_DETAIL])
    assert response.status_code == 302

    response = submit_step_business(steps_data_business[constants.STEP_SALES_VOLUME_BEFORE_BREXIT])
    assert response.status_code == 302

    response = submit_step_business(steps_data_business[constants.STEP_SALES_REVENUE_BEFORE_BREXIT])
    assert response.status_code == 302

    response = submit_step_business(
        {'wizard_save_for_later': True, **steps_data_business[constants.STEP_SALES_AFTER_BREXIT]}
    )
    assert response.status_code == 302
    assert response.url == f'{expected_url}?return_url={return_url}'


def test_save_for_later_no_cache_key(client):
    url = reverse('save-for-later')
    response = client.get(url)

    assert response.status_code == 302
    assert response.url == reverse('landing-page')


@freeze_time("Jan 14th, 2012")
def test_save_for_later(client, steps_data_business, submit_step_business):
    # visit the wizard to create cache entry
    response = submit_step_business({**steps_data_business[constants.STEP_PRODUCT], 'wizard_save_for_later': True})
    assert response.status_code == 302

    url = reverse('save-for-later')
    response = client.get(url)

    assert response.status_code == 200
    assert response.template_name == [views.SaveForLaterFormView.template_name]
    assert response.context_data['form'].initial['expiry_timestamp'] == '17 January 2012 12:00 AM'
    key = helpers.get_user_cache_key(response._request)
    assert response.context_data['form'].initial['url'] == f'http://testserver/triage/user-type/?key={key}'


def test_browse_product(client, steps_data_business, submit_step_business):
    response = submit_step_business({**steps_data_business[constants.STEP_PRODUCT], 'wizard_browse_product': 'root'})
    assert response.status_code == 302

    url = reverse('wizard-business', kwargs={'step': constants.STEP_PRODUCT})
    assert response.url == f'{url}?node_id=root#root'


def test_browse_product_collapse(client, steps_data_business, submit_step_business):
    response = submit_step_business({**steps_data_business[constants.STEP_PRODUCT], 'wizard_browse_product': ''})
    assert response.status_code == 302

    url = reverse('wizard-business', kwargs={'step': constants.STEP_PRODUCT})
    assert response.url == f'{url}#hierarchy-browser'


def test_save_for_later_validation_validation_error(client, steps_data_business, submit_step_business):
    # visit the wizard to create cache entry
    response = submit_step_business({**steps_data_business[constants.STEP_PRODUCT], 'wizard_save_for_later': True})
    assert response.status_code == 302

    # visit the wizard and create cache entry
    url = reverse('save-for-later')
    response = client.post(url)

    assert response.status_code == 200
    assert response.context_data['form'].is_valid() is False


@mock.patch.object(views.SaveForLaterFormView.form_class, 'save')
def test_save_for_later_validation_submit_success(
    mock_save, settings, client,  steps_data_business, submit_step_business
):
    # visit the wizard to create cache entry
    response = submit_step_business({**steps_data_business[constants.STEP_PRODUCT], 'wizard_save_for_later': True})
    assert response.status_code == 302

    mock_save.return_value = create_response()
    url = reverse('save-for-later')
    data = {'email': 'test@example.com'}
    response = client.post(url, data)

    assert response.status_code == 200
    assert response.template_name == views.SaveForLaterFormView.success_template_name
    assert mock_save.call_count == 1
    assert mock_save.call_args == mock.call(
        template_id=settings.GOV_NOTIFY_TEMPLATE_SAVE_FOR_LATER,
        email_address=data['email'],
        form_url=url,
        email_reply_to_id=settings.NO_REPLY_NOTIFICATION_SERVICE_UUID,
    )


@pytest.mark.parametrize('choice,expected_url', (
    (constants.UK_CONSUMER, reverse('wizard-consumer', kwargs={'step': constants.STEP_PRODUCT})),
    (constants.DEVELOPING_COUNTRY_COMPANY, reverse('wizard-developing', kwargs={'step': constants.STEP_COUNTRY})),
))
def test_user_type_routing(client, choice, expected_url, submit_step_routing):
    # USER_TYPE
    response = submit_step_routing({'choice': choice})
    assert response.status_code == 302

    # FINISH
    response = client.get(response.url)

    assert response.status_code == 302
    assert response.url == expected_url


@pytest.mark.parametrize('choice,expected_url', (
    (False, reverse('wizard-business', kwargs={'step': constants.STEP_PRODUCT})),
    (True, reverse('wizard-importer', kwargs={'step': constants.STEP_PRODUCT})),
))
def test_user_type_routing_business(client, choice, expected_url, submit_step_routing):

    # USER_TYPE
    response = client.get(reverse('user-type-routing', kwargs={'step': constants.STEP_USER_TYPE}))
    assert response.status_code == 200
    response = submit_step_routing({'choice': constants.UK_BUSINESS})
    assert response.status_code == 302

    # IMPORT_FROM_OVERSEAS
    response = client.get(response.url)
    assert response.status_code == 200
    response = submit_step_routing({'choice': choice})
    assert response.status_code == 302

    # FINISH
    response = client.get(response.url)

    assert response.status_code == 302
    assert response.url == expected_url


@mock.patch.object(helpers, 'search_hierarchy')
@mock.patch('captcha.fields.ReCaptchaField.clean', mock.Mock)
@mock.patch.object(actions, 'ZendeskAction')
def test_importer_end_to_end(
    mock_zendesk_action, mock_search_hierarchy, submit_step_importer, captcha_stub, client, steps_data_importer
):
    hierarchy = [{'key': 'foo'}]
    mock_search_hierarchy.return_value = create_response({'results': hierarchy})

    # PRODUCT
    response = client.get(reverse('wizard-importer', kwargs={'step': constants.STEP_PRODUCT}))
    assert response.status_code == 200
    assert response.context_data['hierarchy'] == hierarchy
    response = submit_step_importer(steps_data_importer[constants.STEP_PRODUCT])
    assert response.status_code == 302

    # PRODUCT_DETAIL
    response = client.get(response.url)
    assert response.status_code == 200
    response = submit_step_importer(steps_data_importer[constants.STEP_PRODUCT_DETAIL])
    assert response.status_code == 302

    # COUNTRIES_OF_IMPORT
    response = client.get(response.url)
    assert response.status_code == 200
    response = submit_step_importer(steps_data_importer[constants.STEP_COUNTRIES_OF_IMPORT])
    assert response.status_code == 302

    # IMPORTED_PRODUCTS_USAGE
    response = client.get(response.url)
    assert response.status_code == 200
    response = submit_step_importer(steps_data_importer[constants.STEP_IMPORTED_PRODUCTS_USAGE])
    assert response.status_code == 302

    # SALES_VOLUME_BEFORE_BREXIT
    response = client.get(response.url)
    assert response.status_code == 200
    response = submit_step_importer(steps_data_importer[constants.STEP_SALES_VOLUME_BEFORE_BREXIT])
    assert response.status_code == 302

    # SALES_REVENUE_BEFORE_BREXIT
    response = client.get(response.url)
    assert response.status_code == 200
    response = submit_step_importer(steps_data_importer[constants.STEP_SALES_REVENUE_BEFORE_BREXIT])
    assert response.status_code == 302

    # SALES_AFTER_BREXIT
    response = client.get(response.url)
    assert response.status_code == 200
    response = submit_step_importer(steps_data_importer[constants.STEP_SALES_AFTER_BREXIT])
    assert response.status_code == 302

    # MARKET_SIZE_AFTER_BREXIT
    response = client.get(response.url)
    assert response.status_code == 200
    response = submit_step_importer(steps_data_importer[constants.STEP_MARKET_SIZE_AFTER_BREXIT])
    assert response.status_code == 302

    # OTHER_CHANGES
    response = client.get(response.url)
    assert response.status_code == 200
    response = submit_step_importer(steps_data_importer[constants.STEP_OTHER_CHANGES])
    assert response.status_code == 302

    # PRODUCTION_PERCENTAGE
    response = client.get(response.url)
    assert response.status_code == 200
    response = submit_step_importer(steps_data_importer[constants.STEP_PRODUCTION_PERCENTAGE])
    assert response.status_code == 302

    # EQUIVALANT_UK_GOODS
    response = client.get(response.url)
    assert response.status_code == 200
    response = submit_step_importer(steps_data_importer[constants.STEP_EQUIVALANT_UK_GOODS])
    assert response.status_code == 302

    # MARKET_SIZE
    response = client.get(response.url)
    assert response.status_code == 200
    response = submit_step_importer(steps_data_importer[constants.STEP_MARKET_SIZE])
    assert response.status_code == 302

    # OUTCOME
    response = client.get(response.url)
    assert response.status_code == 200
    response = submit_step_importer(steps_data_importer[constants.STEP_OUTCOME])
    assert response.status_code == 302

    # BUSINESS
    response = client.get(response.url)
    assert response.status_code == 200
    response = submit_step_importer(steps_data_importer[constants.STEP_BUSINESS])
    assert response.status_code == 302

    # PERSONAL
    response = client.get(response.url)
    assert response.status_code == 200
    response = submit_step_importer(steps_data_importer[constants.STEP_PERSONAL])
    assert response.status_code == 302

    # SUMMARY
    response = client.get(response.url)
    assert response.status_code == 200
    assert response.context_data['summary'] == {
        'captcha': '-',
        'commodity': {'commodity_code': ['010130', '00', '00'], 'label': 'Asses'},
        'company_name': 'Jim Ham',
        'company_number': '1234567',
        'company_type': 'UK private or public limited company',
        'email': 'jim@example.com',
        'employees': '11-50',
        'employment_regions': ['North East'], 'given_name': 'Jim',
        'equivalent_uk_goods': 'No',
        'equivalent_uk_goods_details': '',
        'family_name': 'Example',
        'has_market_price_changed': "I'm not aware of changes to my prices for these imported goods",
        'has_market_size_changed': "I'm not aware of changes to my sales volumes for these goods",
        'has_other_changes': "I'm not aware of other changes to my business",
        'has_other_changes_type': [],
        'has_price_changed': "I'm not aware of changes to my prices for products related to these goods",
        'has_volume_changed': "I'm not aware of changes to my import volumes for these goods",
        'import_countries': ['France'],
        'imported_good_sector': 'Please select',
        'imported_good_sector_details': '',
        'imported_goods_makes_something_else': 'No',
        'market_price_change_comment': '',
        'market_price_changed_type': [],
        'market_size': 121232,
        'market_size_change_comment': '',
        'market_size_changed_type': [],
        'market_size_known': 'Yes',
        'market_size_year': '2019',
        'other_changes_comment': '',
        'other_information': 'Foo Bar',
        'other_metric_name': '',
        'price_change_comment': '',
        'price_changed_type': [],
        'production_cost_percentage': 23,
        'quarter_four_2018_sales_revenue': 42018,
        'quarter_four_2018_sales_volume': 42018,
        'quarter_one_2019_sales_revenue': 12019,
        'quarter_one_2019_sales_volume': 12019,
        'quarter_three_2019_sales_revenue': 32019,
        'quarter_three_2019_sales_volume': 32019,
        'quarter_two_2019_sales_revenue': 22019,
        'quarter_two_2019_sales_volume': 22019,
        'sales_volume_unit': 'units (number of items)',
        'sector': 'Advanced Engineering',
        'tariff_quota': 'I want the tariff quota decreased',
        'tariff_rate': 'I want the tariff rate decreased',
        'term': '',
        'terms_agreed': '-',
        'turnover': 'under £25,000',
        'volume_changed_type': [],
        'volumes_change_comment': '',
    }

    response = submit_step_importer(steps_data_importer[constants.STEP_SUMMARY])
    assert response.status_code == 302

    # FINISH
    response = client.get(response.url, REMOTE_ADDR='192.168.93.2')
    assert response.status_code == 200
    assert mock_zendesk_action.call_count == 1
    assert mock_zendesk_action.call_args == mock.call(
        subject='ERP form was submitted',
        full_name='Jim Example',
        service_name=constants.ZENDESK_SERVICE_NAME,
        subdomain=settings.ERP_ZENDESK_SUBDOMAIN,
        email_address='jim@example.com',
        form_url=reverse('wizard-importer', kwargs={'step': constants.STEP_SUMMARY}),
        form_session=mock.ANY,
        sender=Sender(
            email_address='jim@example.com',
            country_code=None,
            ip_address='192.168.93.2',
        ),
    )
    assert mock_zendesk_action().save.call_count == 1
    assert mock_zendesk_action().save.call_args == mock.call({
        'commodity': {'commodity_code': ['010130', '00', '00'], 'label': 'Asses'},
        'company_name': 'Jim Ham',
        'company_number': '1234567',
        'company_type': 'LIMITED',
        'email': 'jim@example.com',
        'employees': '11-50',
        'employment_regions': ['NORTH_EAST'],
        'given_name': 'Jim',
        'equivalent_uk_goods': False,
        'family_name': 'Example',
        'has_market_price_changed': False,
        'has_market_size_changed': False,
        'has_other_changes': False,
        'has_price_changed': False,
        'has_volume_changed': False,
        'import_countries': ['FR'],
        'imported_goods_makes_something_else': False,
        'market_size_known': True,
        'other_information': 'Foo Bar',
        'production_cost_percentage': 23,
        'quarter_four_2018_sales_revenue': 42018,
        'quarter_four_2018_sales_volume': 42018,
        'quarter_one_2019_sales_revenue': 12019,
        'quarter_one_2019_sales_volume': 12019,
        'quarter_three_2019_sales_revenue': 32019,
        'quarter_three_2019_sales_volume': 32019,
        'quarter_two_2019_sales_revenue': 22019,
        'quarter_two_2019_sales_volume': 22019,
        'sales_volume_unit': 'UNITS',
        'sector': 'SL10001',
        'tariff_quota': 'DECREASE',
        'tariff_rate': 'DECREASE',
        'turnover': '0-25k',
    })

    # checking details are remembered even after submitting the form
    steps = [
        constants.STEP_PRODUCT,
        constants.STEP_PRODUCT_DETAIL,
        constants.STEP_IMPORTED_PRODUCTS_USAGE,
        constants.STEP_SALES_VOLUME_BEFORE_BREXIT,
        constants.STEP_SALES_REVENUE_BEFORE_BREXIT,
        constants.STEP_SALES_AFTER_BREXIT,
        constants.STEP_MARKET_SIZE_AFTER_BREXIT,
        constants.STEP_OTHER_CHANGES,
        constants.STEP_PRODUCTION_PERCENTAGE,
        constants.STEP_COUNTRIES_OF_IMPORT,
        constants.STEP_EQUIVALANT_UK_GOODS,
        constants.STEP_MARKET_SIZE,
        constants.STEP_OUTCOME,
    ]
    for step in steps:
        response = client.get(reverse('wizard-importer', kwargs={'step': step}))
        assert response.status_code == 200
        assert response.context_data['form'].data == {}

    # BUSINESS
    response = client.get(reverse('wizard-importer', kwargs={'step': constants.STEP_BUSINESS}))
    assert response.status_code == 200
    assert response.context_data['form'].cleaned_data == {
        'company_type': 'LIMITED',
        'company_name': 'Jim Ham',
        'company_number': '1234567',
        'sector': 'SL10001',
        'employees': '11-50',
        'turnover': '0-25k',
        'employment_regions': ['NORTH_EAST']
    }

    # PERSONAL
    response = client.get(reverse('wizard-importer', kwargs={'step': constants.STEP_PERSONAL}))
    assert response.status_code == 200
    assert response.context_data['form'].cleaned_data == {
        'given_name': 'Jim',
        'family_name': 'Example',
        'email': 'jim@example.com',
    }


def test_load_answers_error(client):
    response = client.get(reverse('wizard-importer', kwargs={'step': constants.STEP_PRODUCT}), {'key': '123'})
    assert response.status_code == 200
    assert response.template_name == 'core/invalid-save-for-later-key.html'


def test_load_answers_success(client, submit_step_business, steps_data_business):
    response = submit_step_business(steps_data_business[constants.STEP_PRODUCT])
    assert response.status_code == 302

    response = submit_step_business(steps_data_business[constants.STEP_PRODUCT_DETAIL])
    assert response.status_code == 302

    # save third step with only partial step data
    response = submit_step_business({'sales_volume_unit': 'UNITS', 'wizard_save_for_later': True})

    url = reverse('save-for-later')
    response = client.get(url)
    assert response.status_code == 200

    key = helpers.get_user_cache_key(response._request)
    url = reverse('wizard-business', kwargs={'step': constants.STEP_SALES_VOLUME_BEFORE_BREXIT})

    response = client.get(url, {'key': key})

    assert response.status_code == 200
    assert response.context_data['form'].is_valid() is True
    assert response.context_data['form']['sales_volume_unit'].initial == 'UNITS'
    assert response.context_data['form']['quarter_three_2019_sales_volume'].initial is None


@mock.patch('core.views.ch_search_api_client.company.search_companies')
@mock.patch.object(helpers, 'search_hierarchy')
def test_service_holding_page_redirects(mock_search_hierarchy, mock_search, client, settings):
    mock_search.return_value = create_response({'items': [{'name': 'Smashing corp'}]})
    mock_search_hierarchy.return_value = create_response({'results': [{'key': 'foo'}]})
    urls = [
        reverse('user-type-routing', kwargs={'step': constants.STEP_USER_TYPE}),
        reverse('wizard-business', kwargs={'step': constants.STEP_PRODUCT}),
        reverse('wizard-importer', kwargs={'step': constants.STEP_PRODUCT}),
        reverse('wizard-consumer', kwargs={'step': constants.STEP_PRODUCT}),
        reverse('wizard-developing', kwargs={'step': constants.STEP_COUNTRY}),
        reverse('companies-house-search'),
        reverse('save-for-later'),
    ]

    settings.FEATURE_FLAGS['SERVICE_HOLDING_PAGE_ON'] = True
    reload_urlconf()

    for url in urls:
        response = client.get(url)
        assert response.status_code == 404

    settings.FEATURE_FLAGS['SERVICE_HOLDING_PAGE_ON'] = False
    reload_urlconf()

    for url in urls:
        if url == reverse('companies-house-search'):
            response = client.get(url, data={'term': 'thing'})
        else:
            response = client.get(url)
        assert response.status_code == 200
