import json

from core import forms


def test_product_search_form_no_commodities():
    form = forms.ProductSearchForm({})

    assert form.is_valid() is False
    assert form.errors['term'] == [forms.ProductSearchForm.MESSAGE_MISSING_PRODUCT]


def test_product_search_form():
    commodity = json.dumps({'commodity_code': ['010130', '00', '00'], 'label': 'Asses'})
    form = forms.ProductSearchForm({'commodity': commodity})

    assert form.is_valid() is True
