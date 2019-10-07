from unittest import mock

from directory_constants import choices
from directory_forms_api_client import actions
from directory_forms_api_client.helpers import Sender
import pytest
import requests

from django.core.cache import cache
from django.urls import reverse

from core import constants, forms, helpers, views
from core.tests.helpers import create_response, submit_step_factory


@pytest.fixture
def submit_step_business(client):
    return submit_step_factory(client=client, url_name='wizard-business')


@pytest.fixture
def submit_step_consumer(client):
    return submit_step_factory(client=client, url_name='wizard-consumer')


@pytest.fixture(autouse=True)
def clear_cache():
    cache.clear()


@pytest.fixture(autouse=True)
def mock_lookup_commodity_code_by_name():
    response = create_response({'results': [{'description': 'Example', 'commodity_code': '1234'}]})
    patch = mock.patch.object(helpers, 'lookup_commodity_code_by_name', return_value=response)
    yield patch.start()
    patch.stop()


@pytest.fixture
def steps_data_business(captcha_stub):
    return {
        views.PRODUCT: {'commodities': 'Foo'},
        views.SALES_VOLUME_BEFORE_BREXIT: {
            'sales_volume_unit': 'UNITS',
            'quarter_three_2019': 32019,
            'quarter_two_2019': 22019,
            'quarter_one_2019': 12019,
            'quarter_four_2018': 42018,
        },
        views.SALES_REVENUE_BEFORE_BREXIT: {
            'quarter_three_2019': 32019,
            'quarter_two_2019': 22019,
            'quarter_one_2019': 12019,
            'quarter_four_2018': 42018,
        },
        views.SALES_AFTER_BREXIT: {
            'has_volume_changed': 'False',
            'has_volume_changed_yes': constants.ACTUAL,
            'volumes_change_comment': 'Volume change comment',
            'has_price_changed': 'False',
            'price_change_comment': 'Price change comment',
        },
        views.MARKET_SIZE_AFTER_BREXIT: {
            'has_market_size_changed': 'False',
            'has_market_size_changed_yes': constants.ACTUAL,
            'market_size_change_comment': 'market size change comment',
            'has_market_price_changed': 'False',
            'has_market_price_changed_yes': constants.ACTUAL,
            'market_price_change_comment': 'price change comment',
        },
        views.OTHER_CHANGES: {
            'has_other_changes': 'False',
            'has_other_changes_yes': constants.ACTUAL,
            'other_changes_comment': 'some comment',
        },
        views.MARKET_SIZE: {
            'market_size_known': 'True',
            'market_size_year': '2019',
            'market_size': '121,232',
        },
        views.OTHER_INFOMATION: {
            'other_information': 'Foo Bar',
        },
        views.OUTCOME: {
            'tariff_rate': constants.DECREASE,
            'tariff_quota': constants.DECREASE,
        },
        views.BUSINESS: {
            'company_type': 'LIMITED',
            'company_name': 'Jim Ham',
            'company_number': '1234567',
            'sector': forms.INDUSTRY_CHOICES[1][0],
            'employees': choices.EMPLOYEES[1][0],
            'turnover': forms.TURNOVER_CHOICES[1][0],
            'employment_regions': choices.EXPERTISE_REGION_CHOICES[0][0]
        },
        views.PERSONAL: {
            'given_name': 'Jim',
            'family_name': 'Example',
            'email': 'jim@example.com',
        },
        views.SUMMARY: {
            'terms_agreed': True,
            'g-recaptcha-response': captcha_stub,
        }
    }


@pytest.fixture
def steps_data_consumer(captcha_stub):
    return {
        views.PRODUCT: {
            'commodities': 'Foo'
        },
        views.CONSUMER_CHANGE: {
            'has_price_changed': True,
            'has_choice_changed': False,
            'price_changed_type': constants.ACTUAL,
            'price_change_comment': 'bar',
        },
        views.OTHER_INFOMATION: {
            'other_information': 'Foo Bar',
        },
        views.OUTCOME: {
            'tariff_rate': constants.DECREASE,
            'tariff_quota': constants.DECREASE,
        },
        views.CONSUMER_GROUP: {
            'given_name': 'Jim',
            'family_name': 'Example',
            'email': 'jim@example.com',
            'income_bracket': 'Something',
            'organisation_name': 'Example corp',
            'consumer_regions': choices.EXPERTISE_REGION_CHOICES[0][0],
        },
        views.SUMMARY: {
            'terms_agreed': True,
            'g-recaptcha-response': captcha_stub,
        }
    }


def test_landing_page(client):
    url = reverse('landing-page')
    response = client.get(url)

    assert response.status_code == 200
    assert response.template_name == [views.LandingPage.template_name]


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
@mock.patch('captcha.fields.ReCaptchaField.clean', mock.Mock)
@mock.patch.object(actions, 'ZendeskAction')
def test_business_end_to_end(
    mock_zendesk_action, mock_search_hierarchy, submit_step_business, captcha_stub, client, steps_data_business
):
    hierarchy = [{'key': 'foo'}]
    mock_search_hierarchy.return_value = create_response({'results': hierarchy})

    # PRODUCT
    response = client.get(reverse('wizard-business', kwargs={'step': views.PRODUCT}))
    assert response.status_code == 200
    assert response.context_data['hierarchy'] == hierarchy
    response = submit_step_business(steps_data_business[views.PRODUCT])
    assert response.status_code == 302

    # SALES_VOLUME_BEFORE_BREXIT
    response = client.get(response.url)
    assert response.status_code == 200
    response = submit_step_business(steps_data_business[views.SALES_VOLUME_BEFORE_BREXIT])
    assert response.status_code == 302

    # SALES_REVENUE_BEFORE_BREXIT
    response = client.get(response.url)
    assert response.status_code == 200
    response = submit_step_business(steps_data_business[views.SALES_REVENUE_BEFORE_BREXIT])
    assert response.status_code == 302

    # SALES_AFTER_BREXIT
    response = client.get(response.url)
    assert response.status_code == 200
    response = submit_step_business(steps_data_business[views.SALES_AFTER_BREXIT])
    assert response.status_code == 302

    # MARKET_SIZE_AFTER_BREXIT
    response = client.get(response.url)
    assert response.status_code == 200
    response = submit_step_business(steps_data_business[views.MARKET_SIZE_AFTER_BREXIT])
    assert response.status_code == 302

    # OTHER_CHANGES
    response = client.get(response.url)
    assert response.status_code == 200
    response = submit_step_business(steps_data_business[views.OTHER_CHANGES])
    assert response.status_code == 302

    # MARKET_SIZE
    response = client.get(response.url)
    assert response.status_code == 200
    response = submit_step_business(steps_data_business[views.MARKET_SIZE])
    assert response.status_code == 302

    # OTHER_INFOMATION
    response = client.get(response.url)
    assert response.status_code == 200
    response = submit_step_business(steps_data_business[views.OTHER_INFOMATION])
    assert response.status_code == 302

    # OUTCOME
    response = client.get(response.url)
    assert response.status_code == 200
    response = submit_step_business(steps_data_business[views.OUTCOME])
    assert response.status_code == 302

    # BUSINESS
    response = client.get(response.url)
    assert response.status_code == 200
    response = submit_step_business(steps_data_business[views.BUSINESS])
    assert response.status_code == 302

    # PERSONAL
    response = client.get(response.url)
    assert response.status_code == 200
    response = submit_step_business(steps_data_business[views.PERSONAL])
    assert response.status_code == 302

    # SUMMARY
    response = client.get(response.url)
    assert response.status_code == 200
    assert response.context_data['all_cleaned_data']

    response = submit_step_business(steps_data_business[views.SUMMARY])
    assert response.status_code == 302

    # FINISH
    response = client.get(response.url)

    assert response.status_code == 302
    assert response.url == views.BusinessWizard.success_url
    assert mock_zendesk_action.call_count == 1
    assert mock_zendesk_action.call_args == mock.call(
        subject='ERP form was submitted',
        full_name='Jim Example',
        service_name='erp',
        email_address='jim@example.com',
        form_url=reverse('wizard-business', kwargs={'step': views.SUMMARY}),
        form_session=mock.ANY,
        sender=Sender(
            email_address='jim@example.com',
            country_code=None,
        ),
    )
    assert mock_zendesk_action().save.call_count == 1
    assert mock_zendesk_action().save.call_args == mock.call({
        'commodities': 'Foo',
        'sales_volume_unit': 'UNITS',
        'quarter_three_2019': '32019',
        'quarter_two_2019': '22019',
        'quarter_one_2019': '12019',
        'quarter_four_2018': '42018',
        'has_volume_changed': False,
        'has_price_changed': False,
        'has_market_size_changed': False,
        'has_market_price_changed': False,
        'has_other_changes': False,
        'market_size_known': True,
        'other_information': 'Foo Bar',
        'tariff_rate': 'DECREASE',
        'tariff_quota': 'DECREASE',
        'company_type': 'LIMITED',
        'company_name': 'Jim Ham',
        'company_number': '1234567',
        'sector': 'AEROSPACE',
        'employees': '11-50',
        'turnover': '0-25k',
        'employment_regions': ['NORTH_EAST'],
        'given_name': 'Jim',
        'family_name': 'Example',
        'email': 'jim@example.com'
    })


@mock.patch.object(helpers, 'search_hierarchy')
@mock.patch('captcha.fields.ReCaptchaField.clean', mock.Mock)
@mock.patch.object(actions, 'ZendeskAction')
def test_consumer_end_to_end(
    mock_zendesk_action, mock_search_hierarchy, submit_step_consumer, captcha_stub, client, steps_data_consumer
):
    hierarchy = [{'key': 'foo'}]
    mock_search_hierarchy.return_value = create_response({'results': hierarchy})

    # PRODUCT
    response = client.get(reverse('wizard-consumer', kwargs={'step': views.PRODUCT}))
    assert response.status_code == 200
    assert response.context_data['hierarchy'] == hierarchy
    response = submit_step_consumer(steps_data_consumer[views.PRODUCT])
    assert response.status_code == 302

    # CONSUMER_CHANGE
    response = client.get(response.url)
    assert response.status_code == 200
    response = submit_step_consumer(steps_data_consumer[views.CONSUMER_CHANGE])
    assert response.status_code == 302

    # OTHER_INFOMATION
    response = client.get(response.url)
    assert response.status_code == 200
    response = submit_step_consumer(steps_data_consumer[views.OTHER_INFOMATION])
    assert response.status_code == 302

    # OUTCOME
    response = client.get(response.url)
    assert response.status_code == 200
    response = submit_step_consumer(steps_data_consumer[views.OUTCOME])
    assert response.status_code == 302

    # CONSUMER_GROUP
    response = client.get(response.url)
    assert response.status_code == 200
    response = submit_step_consumer(steps_data_consumer[views.CONSUMER_GROUP])
    assert response.status_code == 302
    # SUMMARY
    response = client.get(response.url)
    assert response.status_code == 200
    assert response.context_data['all_cleaned_data']

    response = submit_step_consumer(steps_data_consumer[views.SUMMARY])
    assert response.status_code == 302

    # FINISH
    response = client.get(response.url)

    assert response.status_code == 302
    assert response.url == views.BusinessWizard.success_url
    assert mock_zendesk_action.call_count == 1
    assert mock_zendesk_action.call_args == mock.call(
        subject='ERP form was submitted',
        full_name='Jim Example',
        service_name='erp',
        email_address='jim@example.com',
        form_url=reverse('wizard-consumer', kwargs={'step': views.SUMMARY}),
        form_session=mock.ANY,
        sender=Sender(
            email_address='jim@example.com',
            country_code=None,
        ),
    )
    assert mock_zendesk_action().save.call_count == 1
    assert mock_zendesk_action().save.call_args == mock.call({
        'commodities': 'Foo',
        'has_price_changed': True,
        'has_choice_changed': False,
        'other_information': 'Foo Bar',
        'tariff_rate': 'DECREASE',
        'tariff_quota': 'DECREASE',
        'given_name': 'Jim',
        'family_name': 'Example',
        'email': 'jim@example.com',
        'income_bracket': 'Something',
        'organisation_name': 'Example corp',
        'consumer_regions': ['NORTH_EAST'],
    })


@mock.patch.object(helpers, 'search_hierarchy')
def test_consumer_end_to_end_nested_validation_error(
    mock_search_hierarchy, submit_step_consumer, client, steps_data_consumer
):
    hierarchy = [{'key': 'foo'}]
    mock_search_hierarchy.return_value = create_response({'results': hierarchy})

    # PRODUCT
    response = client.get(reverse('wizard-business', kwargs={'step': views.PRODUCT}))
    assert response.status_code == 200
    assert response.context_data['hierarchy'] == hierarchy
    response = submit_step_consumer(steps_data_consumer[views.PRODUCT])
    assert response.status_code == 302

    # CONSUMER_CHANGE
    response = client.get(response.url)
    assert response.status_code == 200
    response = submit_step_consumer({'has_price_changed': 'True', 'has_choice_changed': 'False'})
    assert response.status_code == 200
    assert 'has_price_changed' in response.context_data['form'].errors
    assert 'price_changed_type' in response.context_data['form'].fields['has_price_changed'].nested_form.errors
    assert 'price_change_comment' in response.context_data['form'].fields['has_price_changed'].nested_form.errors


def test_wizard_save_for_later(submit_step_business, steps_data_business):
    expected_url = reverse("save-for-later")
    return_url = reverse('wizard-business', kwargs={'step': views.SALES_AFTER_BREXIT})
    response = submit_step_business(steps_data_business[views.PRODUCT])
    assert response.status_code == 302

    response = submit_step_business(steps_data_business[views.SALES_VOLUME_BEFORE_BREXIT])
    assert response.status_code == 302

    response = submit_step_business(steps_data_business[views.SALES_REVENUE_BEFORE_BREXIT])
    assert response.status_code == 302

    response = submit_step_business({'wizard_save_for_later': True, **steps_data_business[views.SALES_AFTER_BREXIT]})
    assert response.status_code == 302
    assert response.url == f'{expected_url}?return_url={return_url}'


def test_save_for_later_no_cache_key(client):
    url = reverse('save-for-later')
    response = client.get(url)

    assert response.status_code == 404


def test_save_for_later(client, steps_data_business, submit_step_business):
    # visit the wizard to create cache entry
    response = submit_step_business({**steps_data_business[views.PRODUCT], 'wizard_save_for_later': True})
    assert response.status_code == 302

    url = reverse('save-for-later')
    response = client.get(url)

    assert response.status_code == 200
    assert response.template_name == [views.SaveForLaterFormView.template_name]


@mock.patch('core.helpers.search_hierarchy')
def test_select_product(mock_search_hierarchy, client, steps_data_business, submit_step_business):
    mock_search_hierarchy.return_value = create_response({'results': []})

    # trigger wizard to take user to first step, then it will remember it's on the first step
    response = client.get(reverse('wizard-business', kwargs={'step': 'foo'}))
    assert response.status_code == 302

    response = submit_step_business({**steps_data_business[views.PRODUCT], 'wizard_select_product': 'Bar'})
    assert response.status_code == 302

    response = client.get(reverse('wizard-business', kwargs={'step': views.PRODUCT}))
    assert response.status_code == 200

    commodities = response.context_data['form'].data['product-search-commodities'].split(views.PRODUCT_DELIMITER)
    assert sorted(commodities) == ['Bar', 'Foo']


@mock.patch('core.helpers.search_hierarchy')
def test_deselect_product(mock_search_hierarchy, client, steps_data_business, submit_step_business):
    mock_search_hierarchy.return_value = create_response({'results': []})

    # trigger wizard to take user to first step, then it will remember it's on the first step
    response = client.get(reverse('wizard-business', kwargs={'step': 'foo'}))
    assert response.status_code == 302

    response = submit_step_business({**steps_data_business[views.PRODUCT], 'wizard_remove_selected_product': 'Foo'})
    assert response.status_code == 302

    response = client.get(reverse('wizard-business', kwargs={'step': views.PRODUCT}))
    assert response.status_code == 200
    assert response.context_data['form'].data['product-search-commodities'] == ''


def test_browse_product(client, steps_data_business, submit_step_business):
    response = submit_step_business({**steps_data_business[views.PRODUCT], 'wizard_browse_product': 'root'})
    assert response.status_code == 302

    url = reverse('wizard-business', kwargs={'step': views.PRODUCT})
    assert response.url == f'{url}?node_id=root#root'


def test_save_for_later_validation_validation_error(client, steps_data_business, submit_step_business):
    # visit the wizard to create cache entry
    response = submit_step_business({**steps_data_business[views.PRODUCT], 'wizard_save_for_later': True})
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
    response = submit_step_business({**steps_data_business[views.PRODUCT], 'wizard_save_for_later': True})
    assert response.status_code == 302

    mock_save.return_value = create_response()
    url = reverse('save-for-later')
    data = {'email': 'test@example.com'}
    response = client.post(url, data)

    assert response.status_code == 302
    assert response.url == views.SaveForLaterFormView.success_url
    assert mock_save.call_count == 1
    assert mock_save.call_args == mock.call(
        template_id=settings.GOV_NOTIFY_TEMPLATE_SAVE_FOR_LATER,
        email_address=data['email'],
        form_url=url,
    )

    response = client.get(response.url)

    for message in response.context['messages']:
        assert str(message) == views.SaveForLaterFormView.success_message


def test_commodity_search_no_term(client):
    url = reverse('commodity-search')
    response = client.get(url)

    assert response.status_code == 400


def test_commodity_search_api_error(mock_lookup_commodity_code_by_name, client, settings):
    mock_lookup_commodity_code_by_name.return_value = create_response(status_code=400)
    url = reverse('commodity-search')

    with pytest.raises(requests.HTTPError):
        client.get(url, data={'term': 'thing'})


def test_commodity_search_api_success(mock_lookup_commodity_code_by_name, client, settings):
    url = reverse('commodity-search')

    response = client.get(url, data={'term': 'thing'})

    assert response.status_code == 200
    assert response.content == b'[{"text":"Example","value":"1234"}]'
    assert mock_lookup_commodity_code_by_name.call_count == 1
    assert mock_lookup_commodity_code_by_name.call_args == mock.call(query='thing')


@pytest.mark.parametrize('choice,expected_url', (
    (constants.UK_BUSINESS, reverse('wizard-business', kwargs={'step': views.PRODUCT})),
    (constants.UK_CONSUMER, reverse('wizard-consumer', kwargs={'step': views.PRODUCT})),
))
def test_user_type_routing(client, choice, expected_url):
    url = reverse('user-type-routing')

    response = client.post(url, {'choice': choice})

    assert response.status_code == 302
    assert response.url == expected_url
