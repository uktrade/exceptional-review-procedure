from core import forms


def test_product_search_form_no_commodities():
    form = forms.ProductSearchForm({})

    assert form.is_valid() is False
    assert form.errors['term'] == [forms.ProductSearchForm.MESSAGE_MISSING_PRODUCT]


def test_product_search_form():
    form = forms.ProductSearchForm({'commodities': 'Foo'})

    assert form.is_valid() is True
