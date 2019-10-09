from urllib.parse import quote, unquote

from directory_ch_client.client import ch_search_api_client
from directory_forms_api_client import actions
from directory_forms_api_client.helpers import FormSessionMixin, Sender
from formtools.wizard.views import NamedUrlSessionWizardView
from formtools.wizard.forms import ManagementForm
from formtools.wizard.views import normalize_name
from rest_framework.generics import GenericAPIView
from rest_framework.response import Response

from django.conf import settings
from django.contrib.messages.views import SuccessMessageMixin
from django.core.exceptions import SuspiciousOperation
from django.core.paginator import Paginator
from django.shortcuts import redirect, Http404
from django.urls import reverse, reverse_lazy
from django.views.generic import FormView, TemplateView

from core import constants, forms, helpers, serializers


BUSINESS = 'business'
CONSUMER_CHANGE = 'consumer-change'
CONSUMER_GROUP = 'consumers'
COUNTRIES_OF_IMPORT = 'which-countries'
COUNTRY = 'country'
EQUIVALANT_UK_GOODS = 'equivalent-uk-goods'
IMPORT_FROM_OVERSEAS = 'import-from-overseas'
IMPORTED_PRODUCTS_USAGE = 'imported-products-usage'
MARKET_SIZE = 'market-size'
MARKET_SIZE_AFTER_BREXIT = 'market-size-after-brexit'
OTHER_CHANGES = 'other-changes-after-brexit'
OTHER_INFOMATION = 'other-information'
OUTCOME = 'outcome'
PERSONAL = 'personal'
PRODUCT = 'product-search'
PRODUCTION_PERCENTAGE = 'production-percentage'
SALES_AFTER_BREXIT = 'sales-after-brexit'
SALES_REVENUE_BEFORE_BREXIT = 'sales-revenue-before-brexit'
SALES_VOLUME_BEFORE_BREXIT = 'sales-volume-before-brexit'
SUMMARY = 'summary'
USER_TYPE = 'user-type'


class LandingPage(TemplateView):
    template_name = 'core/landing-page.html'


class RoutingWizardView(NamedUrlSessionWizardView):
    storage_name = 'core.helpers.NoResetStorage'
    form_list = (
        (USER_TYPE, forms.RoutingUserTypeForm),
        (IMPORT_FROM_OVERSEAS, forms.RoutingImportFromOverseasForm),
    )
    templates = {
        USER_TYPE: 'core/wizard-step-user-type-routing.html',
        IMPORT_FROM_OVERSEAS: 'core/wizard-step-import-from-overseas.html',
    }

    def condition_import_from_overseas(self):
        cleaned_data = self.get_cleaned_data_for_step(USER_TYPE) or {}
        return cleaned_data.get('choice') == constants.UK_BUSINESS

    condition_dict = {IMPORT_FROM_OVERSEAS: condition_import_from_overseas}

    def get_template_names(self):
        return [self.templates[self.steps.current]]

    def done(self, form_list, form_dict, **kwargs):
        user_type = form_dict[USER_TYPE].cleaned_data['choice']
        if user_type == constants.UK_BUSINESS:
            import_from_overseas = form_dict[IMPORT_FROM_OVERSEAS].cleaned_data['choice']
            if import_from_overseas:
                url = reverse('wizard-importer', kwargs={'step': PRODUCT})
            else:
                url = reverse('wizard-business', kwargs={'step': PRODUCT})
        elif user_type == constants.UK_CONSUMER:
            url = reverse('wizard-consumer', kwargs={'step': PRODUCT})
        elif user_type == constants.DEVELOPING_COUNTRY_COMPANY:
            url = reverse('wizard-developing', kwargs={'step': COUNTRY})
        else:
            raise NotImplementedError
        return redirect(url)


class BaseWizard(FormSessionMixin, NamedUrlSessionWizardView):
    storage_name = 'core.helpers.CacheStorage'
    success_url = reverse_lazy('submitted')

    def dispatch(self, request, *args, **kwargs):
        if 'key' in self.request.GET:
            helpers.load_saved_submission(
                request=request,
                prefix=self.get_prefix(request, *args, **kwargs),
                key=self.request.GET['key']
            )
        return super().dispatch(request=request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        management_form = ManagementForm(self.request.POST, prefix=self.prefix)
        if not management_form.is_valid():
            raise SuspiciousOperation('ManagementForm data is missing or has been tampered.')
        self.storage.current_step = management_form.cleaned_data['current_step']
        if request.POST.get('wizard_save_for_later'):
            self.storage.set_step_data(self.steps.current, request.POST)
            self.storage.mark_shared()
            url = reverse('save-for-later')
            return_url = quote(self.get_step_url(self.steps.current))
            return redirect(f'{url}?return_url={return_url}')
        elif request.POST.get('wizard_browse_product'):
            self.storage.set_step_data(self.steps.current, request.POST)
            url = self.get_step_url(PRODUCT)
            node_id = request.POST['wizard_browse_product']
            return redirect(f'{url}?node_id={node_id}#{node_id}')
        elif request.POST.get('wizard_select_product'):
            data = request.POST.copy()
            commodities = self.get_selected_commodities(data)
            commodities.append(data['wizard_select_product'])
            self.set_selected_commodities(data=data, commodities=commodities)
            return redirect(self.get_step_url(PRODUCT))
        elif request.POST.get('wizard_remove_selected_product'):
            data = request.POST.copy()
            commodities = self.get_selected_commodities(data)
            commodities.remove(data['wizard_remove_selected_product'])
            self.set_selected_commodities(data=data, commodities=commodities)
            return redirect(self.get_step_url(PRODUCT))
        return super().post(request=request, *args, **kwargs)

    def get_template_names(self):
        return [self.templates[self.steps.current]]

    def get_context_data(self, form, **kwargs):
        context = super().get_context_data(form=form, **kwargs)
        if self.steps.current == SUMMARY:
            summary = {}
            for form_key in self.get_form_list():
                form_obj = self.get_form(
                    step=form_key,
                    data=self.storage.get_step_data(form_key),
                )
                if form_obj.is_valid():
                    summary.update(forms.get_display_data(form_obj))
            summary['commodities'] = helpers.parse_commodities(summary['commodities'])
            context['summary'] = summary
        elif self.steps.current == PRODUCT:
            if self.request.GET.get('product-search-term'):
                response = helpers.lookup_commodity_code_by_name(
                    query=self.request.GET['product-search-term'],
                    page=self.request.GET.get('page', 1),
                )
                response.raise_for_status()
                parsed = response.json()
                context['search'] = parsed
                context['term'] = self.request.GET['product-search-term']
                paginator = Paginator(range(parsed['total_results']), 20)
                context['paginator_page'] = paginator.get_page(self.request.GET.get('page', 1))
                context['pagination_url'] = helpers.get_paginator_url(
                    filters=self.request.GET,
                    url=self.get_step_url(PRODUCT)
                )

            response = helpers.search_hierarchy(self.request.GET.get('node_id', 'root'))
            response.raise_for_status()
            context['hierarchy'] = response.json()['results']
            data = self.storage.get_step_data(self.steps.current) or {}
            context['commodities'] = self.get_selected_commodities(data)
        return context

    def done(self, form_list, **kwargs):
        form_data = self.serialize_form_list(form_list)
        sender = Sender(
            email_address=form_data['email'],
            country_code=None,
        )
        action = actions.ZendeskAction(
            subject='ERP form was submitted',
            full_name=form_data['given_name'] + ' ' + form_data['family_name'],
            service_name='erp',
            email_address=form_data['email'],
            form_url=self.get_step_url(SUMMARY),
            form_session=self.form_session,
            sender=sender,
        )
        response = action.save(form_data)
        response.raise_for_status()
        return redirect(self.success_url)

    @staticmethod
    def get_selected_commodities(data):
        return helpers.parse_commodities(data.get('product-search-commodities'))

    def set_selected_commodities(self, data, commodities):
        data['product-search-commodities'] = helpers.PRODUCT_DELIMITER.join(list(set(commodities)))
        self.storage.set_step_data(self.steps.current, data)

    def serialize_form_list(self, form_list):
        data = {}
        for form in form_list:
            data.update(form.cleaned_data)
        del data['terms_agreed']
        del data['captcha']
        del data['term']
        return data


class BusinessWizard(BaseWizard):
    form_list = (
        (PRODUCT, forms.ProductSearchForm),
        (SALES_VOLUME_BEFORE_BREXIT, forms.SalesVolumeBeforeBrexitForm),
        (SALES_REVENUE_BEFORE_BREXIT, forms.SalesRevenueBeforeBrexitForm),
        (SALES_AFTER_BREXIT, forms.SalesAfterBrexitForm),
        (MARKET_SIZE_AFTER_BREXIT, forms.MarketSizeAfterBrexitForm),
        (OTHER_CHANGES, forms.OtherChangesAfterBrexitForm),
        (MARKET_SIZE, forms.MarketSizeForm),
        (OTHER_INFOMATION, forms.OtherInformationForm),
        (OUTCOME, forms.OutcomeForm),
        (BUSINESS, forms.BusinessDetailsForm),
        (PERSONAL, forms.PersonalDetailsForm),
        (SUMMARY, forms.SummaryForm),
    )

    templates = {
        PRODUCT: 'core/wizard-step-product.html',
        SALES_VOLUME_BEFORE_BREXIT: 'core/wizard-step-sales-volume-before-brexit.html',
        SALES_REVENUE_BEFORE_BREXIT: 'core/wizard-step-sales-revenue-before-brexit.html',
        SALES_AFTER_BREXIT: 'core/wizard-step-sales-after-brexit.html',
        MARKET_SIZE_AFTER_BREXIT: 'core/wizard-step-market-size-after-brexit.html',
        OTHER_CHANGES: 'core/wizard-step-other-changes-after-brexit.html',
        MARKET_SIZE: 'core/wizard-step-market-size.html',
        OTHER_INFOMATION: 'core/wizard-step-other-information.html',
        OUTCOME: 'core/wizard-step-outcome.html',
        BUSINESS: 'core/wizard-step-business.html',
        PERSONAL: 'core/wizard-step-personal.html',
        SUMMARY: 'core/wizard-step-summary-uk-business.html',
    }


class ImporterWizard(BaseWizard):
    form_list = (
        (PRODUCT, forms.ProductSearchForm),
        (IMPORTED_PRODUCTS_USAGE, forms.ImportedProductsUsageForm),
        (SALES_VOLUME_BEFORE_BREXIT, forms.SalesVolumeBeforeBrexitForm),
        (SALES_REVENUE_BEFORE_BREXIT, forms.SalesRevenueBeforeBrexitForm),
        (SALES_AFTER_BREXIT, forms.SalesAfterBrexitForm),
        (MARKET_SIZE_AFTER_BREXIT, forms.MarketSizeAfterBrexitForm),
        (OTHER_CHANGES, forms.OtherChangesAfterBrexitForm),
        (PRODUCTION_PERCENTAGE, forms.ProductionPercentageForm),
        (COUNTRIES_OF_IMPORT, forms.CountriesImportSourceForm),
        (EQUIVALANT_UK_GOODS, forms.EquivalendUKGoodsForm),
        (MARKET_SIZE, forms.MarketSizeForm),
        (OTHER_INFOMATION, forms.OtherInformationForm),
        (OUTCOME, forms.OutcomeForm),
        (BUSINESS, forms.BusinessDetailsForm),
        (PERSONAL, forms.PersonalDetailsForm),
        (SUMMARY, forms.SummaryForm),
    )
    templates = {
        PRODUCT: 'core/wizard-step-product.html',
        IMPORTED_PRODUCTS_USAGE: 'core/wizard-step-importer-products-usage.html',
        SALES_VOLUME_BEFORE_BREXIT: 'core/wizard-step-sales-volume-before-brexit.html',
        SALES_REVENUE_BEFORE_BREXIT: 'core/wizard-step-sales-revenue-before-brexit.html',
        SALES_AFTER_BREXIT: 'core/wizard-step-sales-after-brexit.html',
        MARKET_SIZE_AFTER_BREXIT: 'core/wizard-step-market-size-after-brexit.html',
        OTHER_CHANGES: 'core/wizard-step-other-changes-after-brexit.html',
        PRODUCTION_PERCENTAGE: 'core/wizard-step-production-percentage.html',
        COUNTRIES_OF_IMPORT: 'core/wizard-step-country-import-country.html',
        EQUIVALANT_UK_GOODS: 'core/wizard-step-equivalent-uk-goods.html',
        MARKET_SIZE: 'core/wizard-step-market-size.html',
        OTHER_INFOMATION: 'core/wizard-step-other-information.html',
        OUTCOME: 'core/wizard-step-outcome.html',
        BUSINESS: 'core/wizard-step-business.html',
        PERSONAL: 'core/wizard-step-personal.html',
        SUMMARY: 'core/wizard-step-summary-importer.html',
    }

    def get_prefix(self, request, *args, **kwargs):
        # share the answers with business view
        return normalize_name(BusinessWizard.__name__)


class ConsumerWizard(BaseWizard):
    form_list = (
        (PRODUCT, forms.ProductSearchForm),
        (CONSUMER_CHANGE, forms.ConsumerChangeForm),
        (OTHER_INFOMATION, forms.OtherInformationForm),
        (OUTCOME, forms.OutcomeForm),
        (CONSUMER_GROUP, forms.ConsumerGroupForm),
        (SUMMARY, forms.SummaryForm),
    )

    templates = {
        PRODUCT: 'core/wizard-step-product.html',
        CONSUMER_CHANGE: 'core/wizard-step-consumer-change.html',
        OTHER_INFOMATION: 'core/wizard-step-other-information.html',
        OUTCOME: 'core/wizard-step-outcome.html',
        CONSUMER_GROUP: 'core/wizard-step-consumer-group.html',
        SUMMARY: 'core/wizard-step-summary-consumer.html',
    }


class DevelopingCountryWizard(BaseWizard):
    form_list = (
        (COUNTRY, forms.DevelopingCountryForm),
        (PRODUCT, forms.ProductSearchForm),
        (SALES_VOLUME_BEFORE_BREXIT, forms.SalesVolumeBeforeBrexitForm),
        (SALES_REVENUE_BEFORE_BREXIT, forms.SalesRevenueBeforeBrexitForm),
        (SALES_AFTER_BREXIT, forms.SalesAfterBrexitForm),
        (MARKET_SIZE_AFTER_BREXIT, forms.MarketSizeAfterBrexitForm),
        (OTHER_CHANGES, forms.OtherChangesAfterBrexitForm),
        (OUTCOME, forms.OutcomeForm),
        (BUSINESS, forms.BusinessDetailsDevelopingCountryForm),
        (PERSONAL, forms.PersonalDetailsForm),
        (SUMMARY, forms.SummaryForm),

    )
    templates = {
        COUNTRY: 'core/wizard-step-developing-country.html',
        PRODUCT: 'core/wizard-step-product.html',
        SALES_VOLUME_BEFORE_BREXIT: 'core/wizard-step-sales-volume-before-brexit.html',
        SALES_REVENUE_BEFORE_BREXIT: 'core/wizard-step-sales-revenue-before-brexit.html',
        SALES_AFTER_BREXIT: 'core/wizard-step-sales-after-brexit.html',
        MARKET_SIZE_AFTER_BREXIT: 'core/wizard-step-market-size-after-brexit.html',
        OTHER_CHANGES: 'core/wizard-step-other-changes-after-brexit.html',
        OUTCOME: 'core/wizard-step-outcome.html',
        BUSINESS: 'core/wizard-step-business.html',
        PERSONAL: 'core/wizard-step-personal.html',
        SUMMARY: 'core/wizard-step-summary-developing-country.html',
    }


class CompaniesHouseSearchAPIView(GenericAPIView):
    serializer_class = serializers.CompaniesHouseSearchSerializer
    permission_classes = []
    authentication_classes = []

    def get(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.GET)
        serializer.is_valid(raise_exception=True)
        response = ch_search_api_client.company.search_companies(query=serializer.validated_data['term'])
        response.raise_for_status()
        return Response(response.json()['items'])


class CommodityCodeSearchAPIView(GenericAPIView):
    serializer_class = serializers.CommodityCodeSearchSerializer
    permission_classes = []
    authentication_classes = []

    def get(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.GET)
        serializer.is_valid(raise_exception=True)
        response = helpers.lookup_commodity_code_by_name(query=serializer.validated_data['term'])
        response.raise_for_status()
        results = [
            {'text': result['description'], 'value': result['commodity_code']}
            for result in response.json()['results']
        ]
        return Response(results)


class SaveForLaterFormView(SuccessMessageMixin, FormView):
    form_class = forms.SaveForLaterForm
    template_name = 'core/save-for-later.html'
    success_url = reverse_lazy('landing-page')
    success_message = 'Response saved. Check your emails.'

    @property
    def return_url(self):
        default_url = reverse('user-type-routing', kwargs={'step': USER_TYPE})
        return unquote(self.request.GET.get('return_url', '')) or default_url

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        user_cache_key = helpers.get_user_cache_key(self.request)
        if not user_cache_key:
            raise Http404()
        url = self.request.build_absolute_uri(self.return_url)
        kwargs['return_url'] = f'{url}?key={user_cache_key}'
        return kwargs

    def form_valid(self, form):
        response = form.save(
            template_id=settings.GOV_NOTIFY_TEMPLATE_SAVE_FOR_LATER,
            email_address=form.cleaned_data['email'],
            form_url=self.request.get_full_path(),
        )
        response.raise_for_status()
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        return super().get_context_data(return_url=self.return_url)
