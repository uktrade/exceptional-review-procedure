from urllib.parse import quote, unquote

from directory_ch_client.client import ch_search_api_client
from directory_forms_api_client import actions
from directory_forms_api_client.helpers import FormSessionMixin, Sender
from formtools.wizard.views import NamedUrlSessionWizardView
from rest_framework.generics import GenericAPIView
from rest_framework.response import Response

from django.conf import settings
from django.contrib.messages.views import SuccessMessageMixin
from django.core.paginator import Paginator
from django.shortcuts import redirect, Http404
from django.urls import reverse, reverse_lazy
from django.views.generic import FormView, TemplateView

from core import constants, forms, helpers, serializers


PRODUCT = 'product-search'
IMPORT_FROM_OVERSEAS = 'import-from-overseas'
SALES_VOLUME_BEFORE_BREXIT = 'sales-volume-before-brexit'
SALES_REVENUE_BEFORE_BREXIT = 'sales-revenue-before-brexit'
SALES_AFTER_BREXIT = 'sales-after-brexit'
MARKET_SIZE_AFTER_BREXIT = 'market-size-after-brexit'
OTHER_CHANGES = 'other-changes-after-brexit'
MARKET_SIZE = 'market-size'
OTHER_INFOMATION = 'other-information'
CONSUMER_GROUP = 'consumers'
CONSUMER_CHANGE = 'consumer-change'

OUTCOME = 'outcome'
BUSINESS = 'business'
PERSONAL = 'personal'
SUMMARY = 'summary'
# unusual character that is unlikely to be included in each product label
PRODUCT_DELIMITER = 'µ'


class LandingPage(TemplateView):
    template_name = 'core/landing-page.html'


class RoutingFormView(FormView):
    form_class = forms.RoutingForm
    template_name = 'core/user-type-routing.html'

    def form_valid(self, form):
        if form.cleaned_data['choice'] == constants.UK_BUSINESS:
            url = reverse('wizard-business', kwargs={'step': PRODUCT})
        elif form.cleaned_data['choice'] == constants.UK_CONSUMER:
            url = reverse('wizard-consumer', kwargs={'step': PRODUCT})
        else:
            raise NotImplementedError
        return redirect(url)


class BaseWizard(FormSessionMixin, NamedUrlSessionWizardView):
    storage_name = 'core.helpers.CacheStorage'
    success_url = reverse_lazy('submitted')

    def dispatch(self, request, *args, **kwargs):
        if 'key' in self.request.GET:
            helpers.load_saved_submission(request=request, key=self.request.GET['key'])
        return super().dispatch(request=request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
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
            context['all_cleaned_data'] = self.get_all_cleaned_data()
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
        commodities = data.get('product-search-commodities')
        return commodities.split(PRODUCT_DELIMITER) if commodities else []

    def set_selected_commodities(self, data, commodities):
        data['product-search-commodities'] = PRODUCT_DELIMITER.join(list(set(commodities)))
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
        SUMMARY: 'core/wizard-step-summary.html',
    }


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
        SUMMARY: 'core/wizard-step-summary.html',
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
        return unquote(self.request.GET.get('return_url', '')) or reverse('user-type-routing')

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
