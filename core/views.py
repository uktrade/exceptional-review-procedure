import datetime
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
from django.core.exceptions import SuspiciousOperation
from django.core.paginator import Paginator
from django.shortcuts import redirect, Http404
from django.template.response import TemplateResponse
from django.urls import reverse, reverse_lazy
from django.utils import timezone
from django.views.generic import FormView, TemplateView

from core import constants, forms, helpers, serializers


class LandingPageView(TemplateView):
    template_name = 'core/landing-page.html'


class PrivacyPolicyView(TemplateView):
    template_name = 'core/privacy-policy.html'


class CookiesView(TemplateView):
    template_name = 'core/cookies.html'


class RoutingWizardView(NamedUrlSessionWizardView):
    storage_name = 'core.helpers.NoResetStorage'
    form_list = (
        (constants.STEP_USER_TYPE, forms.RoutingUserTypeForm),
        (constants.STEP_IMPORT_FROM_OVERSEAS, forms.RoutingImportFromOverseasForm),
    )
    templates = {
        constants.STEP_USER_TYPE: 'core/wizard-step-user-type-routing.html',
        constants.STEP_IMPORT_FROM_OVERSEAS: 'core/wizard-step-import-from-overseas.html',
    }

    def condition_import_from_overseas(self):
        cleaned_data = self.get_cleaned_data_for_step(constants.STEP_USER_TYPE) or {}
        return cleaned_data.get('choice') == constants.UK_BUSINESS

    condition_dict = {
        constants.STEP_IMPORT_FROM_OVERSEAS: condition_import_from_overseas
    }

    def get_template_names(self):
        return [self.templates[self.steps.current]]

    def done(self, form_list, form_dict, **kwargs):
        user_type = form_dict[constants.STEP_USER_TYPE].cleaned_data['choice']
        if user_type == constants.UK_BUSINESS:
            import_from_overseas = form_dict[constants.STEP_IMPORT_FROM_OVERSEAS].cleaned_data['choice']
            if import_from_overseas:
                url = reverse('wizard-importer', kwargs={'step': constants.STEP_PRODUCT})
            else:
                url = reverse('wizard-business', kwargs={'step': constants.STEP_PRODUCT})
        elif user_type == constants.UK_CONSUMER:
            url = reverse('wizard-consumer', kwargs={'step': constants.STEP_PRODUCT})
        elif user_type == constants.DEVELOPING_COUNTRY_COMPANY:
            url = reverse('wizard-developing', kwargs={'step': constants.STEP_COUNTRY})
        else:
            raise NotImplementedError
        return redirect(url)


class BaseWizard(FormSessionMixin, NamedUrlSessionWizardView):
    storage_name = 'core.helpers.CacheStorage'

    def dispatch(self, request, *args, **kwargs):
        if 'key' in self.request.GET:
            try:
                helpers.load_saved_submission(
                    request=request,
                    prefix=self.get_prefix(request, *args, **kwargs),
                    key=self.request.GET['key']
                )
            except Http404:
                return TemplateResponse(self.request, 'core/invalid-save-for-later-key.html', {})
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
            url = self.get_step_url(constants.STEP_PRODUCT)
            node_id = request.POST['wizard_browse_product']
            return redirect(f'{url}?node_id={node_id}#{node_id}')
        return super().post(request=request, *args, **kwargs)

    def get_template_names(self):
        return [self.templates[self.steps.current]]

    def get_summary(self):
        labels = {}
        values = {}
        for form_key in self.get_form_list():
            form_obj = self.get_form(step=form_key, data=self.storage.get_step_data(form_key))
            labels.update(helpers.get_form_display_data(form_obj))
            values.update(helpers.get_form_cleaned_data(form_obj))
        return labels, values

    def get_context_data(self, form, **kwargs):
        context = super().get_context_data(form=form, **kwargs)
        if self.steps.current == constants.STEP_SUMMARY:
            context['summary'], context['form_values'] = self.get_summary()
        elif self.steps.current == constants.STEP_PRODUCT:
            term = self.request.GET.get('product-search-term')
            if term:
                is_lookup_by_code = term.isdigit()
                if is_lookup_by_code:
                    response = helpers.search_commodity_by_code(code=term)
                else:
                    page = self.request.GET.get('page', 1)
                    response = helpers.search_commodity_by_term(term=term, page=page)
                response.raise_for_status()
                parsed = response.json()
                context['search'] = parsed
                context['term'] = term
                if not is_lookup_by_code:
                    total_results = parsed['total_results']
                    paginator = Paginator(range(total_results), 20)
                    context['paginator_page'] = paginator.get_page(self.request.GET.get('page', 1))
                    context['pagination_url'] = helpers.get_paginator_url(
                        filters=self.request.GET,
                        url=self.get_step_url(constants.STEP_PRODUCT)
                    )
            response = helpers.search_hierarchy(self.request.GET.get('node_id', 'root'))
            response.raise_for_status()
            context['hierarchy'] = response.json()['results']
        elif self.steps.current == constants.STEP_PRODUCT_DETAIL:
            step_data = self.get_cleaned_data_for_step(constants.STEP_PRODUCT)
            context['commodity'] = step_data['commodity'] if step_data else None
        return context

    def done(self, form_list, **kwargs):
        form_data = self.serialize_form_list(form_list)
        sender = Sender(
            email_address=form_data['email'],
            country_code=None,
            ip_address=helpers.get_sender_ip_address(self.request),
        )
        action = actions.ZendeskAction(
            subject='ERP form was submitted',
            full_name=form_data['given_name'] + ' ' + form_data['family_name'],
            service_name='erp',
            email_address=form_data['email'],
            form_url=self.get_step_url(constants.STEP_SUMMARY),
            form_session=self.form_session,
            sender=sender,
        )
        response = action.save(form_data)
        response.raise_for_status()
        template_name = self.templates[constants.STEP_FINISHED]
        context = self.get_context_data(form=None)
        context['summary'], context['form_values'] = self.get_summary()
        context['summary_template'] = self.summary_template
        return TemplateResponse(self.request, [template_name], context)

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
        (constants.STEP_PRODUCT, forms.ProductSearchForm),
        (constants.STEP_PRODUCT_DETAIL, forms.NoOperationForm),
        (constants.STEP_SALES_VOLUME_BEFORE_BREXIT, forms.SalesVolumeBeforeBrexitForm),
        (constants.STEP_SALES_REVENUE_BEFORE_BREXIT, forms.SalesRevenueBeforeBrexitForm),
        (constants.STEP_SALES_AFTER_BREXIT, forms.SalesAfterBrexitForm),
        (constants.STEP_MARKET_SIZE_AFTER_BREXIT, forms.MarketSizeAfterBrexitForm),
        (constants.STEP_OTHER_CHANGES, forms.OtherChangesAfterBrexitForm),
        (constants.STEP_MARKET_SIZE, forms.MarketSizeForm),
        (constants.STEP_OUTCOME, forms.OutcomeForm),
        (constants.STEP_BUSINESS, forms.BusinessDetailsForm),
        (constants.STEP_PERSONAL, forms.PersonalDetailsForm),
        (constants.STEP_SUMMARY, forms.SummaryForm),
    )
    templates = {
        constants.STEP_PRODUCT: 'core/wizard-step-product.html',
        constants.STEP_PRODUCT_DETAIL: 'core/wizard-step-product-detail.html',
        constants.STEP_SALES_VOLUME_BEFORE_BREXIT: 'core/wizard-step-sales-volume-before-brexit.html',
        constants.STEP_SALES_REVENUE_BEFORE_BREXIT: 'core/wizard-step-sales-revenue-before-brexit.html',
        constants.STEP_SALES_AFTER_BREXIT: 'core/wizard-step-sales-after-brexit.html',
        constants.STEP_MARKET_SIZE_AFTER_BREXIT: 'core/wizard-step-market-size-after-brexit.html',
        constants.STEP_OTHER_CHANGES: 'core/wizard-step-other-changes-after-brexit.html',
        constants.STEP_MARKET_SIZE: 'core/wizard-step-market-size.html',
        constants.STEP_OUTCOME: 'core/wizard-step-outcome.html',
        constants.STEP_BUSINESS: 'core/wizard-step-business.html',
        constants.STEP_PERSONAL: 'core/wizard-step-personal.html',
        constants.STEP_SUMMARY: 'core/wizard-step-summary-uk-business.html',
        constants.STEP_FINISHED: 'core/form-submitted.html',
    }
    summary_template = 'core/summary/report-uk-business.html'


class ImporterWizard(BaseWizard):
    form_list = (
        (constants.STEP_PRODUCT, forms.ProductSearchForm),
        (constants.STEP_PRODUCT_DETAIL, forms.NoOperationForm),
        (constants.STEP_COUNTRIES_OF_IMPORT, forms.CountriesImportSourceForm),
        (constants.STEP_IMPORTED_PRODUCTS_USAGE, forms.ImportedProductsUsageForm),
        (constants.STEP_SALES_VOLUME_BEFORE_BREXIT, forms.SalesVolumeBeforeBrexitForm),
        (constants.STEP_SALES_REVENUE_BEFORE_BREXIT, forms.SalesRevenueBeforeBrexitForm),
        (constants.STEP_SALES_AFTER_BREXIT, forms.SalesAfterBrexitForm),
        (constants.STEP_MARKET_SIZE_AFTER_BREXIT, forms.MarketSizeAfterBrexitForm),
        (constants.STEP_OTHER_CHANGES, forms.OtherChangesAfterBrexitForm),
        (constants.STEP_PRODUCTION_PERCENTAGE, forms.ProductionPercentageForm),
        (constants.STEP_EQUIVALANT_UK_GOODS, forms.EquivalendUKGoodsForm),
        (constants.STEP_MARKET_SIZE, forms.MarketSizeForm),
        (constants.STEP_OUTCOME, forms.OutcomeForm),
        (constants.STEP_BUSINESS, forms.BusinessDetailsForm),
        (constants.STEP_PERSONAL, forms.PersonalDetailsForm),
        (constants.STEP_SUMMARY, forms.SummaryForm),
    )
    templates = {
        constants.STEP_PRODUCT: 'core/wizard-step-product.html',
        constants.STEP_PRODUCT_DETAIL: 'core/wizard-step-product-detail.html',
        constants.STEP_IMPORTED_PRODUCTS_USAGE: 'core/wizard-step-importer-products-usage.html',
        constants.STEP_SALES_VOLUME_BEFORE_BREXIT: 'core/wizard-step-sales-volume-before-brexit.html',
        constants.STEP_SALES_REVENUE_BEFORE_BREXIT: 'core/wizard-step-sales-revenue-before-brexit.html',
        constants.STEP_SALES_AFTER_BREXIT: 'core/wizard-step-sales-after-brexit.html',
        constants.STEP_MARKET_SIZE_AFTER_BREXIT: 'core/wizard-step-market-size-after-brexit.html',
        constants.STEP_OTHER_CHANGES: 'core/wizard-step-other-changes-after-brexit.html',
        constants.STEP_PRODUCTION_PERCENTAGE: 'core/wizard-step-production-percentage.html',
        constants.STEP_COUNTRIES_OF_IMPORT: 'core/wizard-step-country-import-country.html',
        constants.STEP_EQUIVALANT_UK_GOODS: 'core/wizard-step-equivalent-uk-goods.html',
        constants.STEP_MARKET_SIZE: 'core/wizard-step-market-size.html',
        constants.STEP_OUTCOME: 'core/wizard-step-outcome.html',
        constants.STEP_BUSINESS: 'core/wizard-step-business.html',
        constants.STEP_PERSONAL: 'core/wizard-step-personal.html',
        constants.STEP_SUMMARY: 'core/wizard-step-summary-importer.html',
        constants.STEP_FINISHED: 'core/form-submitted.html',
    }
    summary_template = 'core/summary/report-importer.html'

    def get_prefix(self, request, *args, **kwargs):
        # share the answers with business view
        return normalize_name(BusinessWizard.__name__)


class ConsumerWizard(BaseWizard):
    form_list = (
        (constants.STEP_PRODUCT, forms.ProductSearchForm),
        (constants.STEP_PRODUCT_DETAIL, forms.NoOperationForm),
        (constants.STEP_CONSUMER_CHANGE, forms.ConsumerChangeForm),
        (constants.STEP_OTHER_CHANGES, forms.OtherInformationForm),
        (constants.STEP_CONSUMER_TYPE, forms.ConsumerTypeForm),
        (constants.STEP_PERSONAL, forms.ConsumerPersonalDetailsForm),
        (constants.STEP_CONSUMER_GROUP, forms.ConsumerGroupForm),
        (constants.STEP_SUMMARY, forms.SummaryForm),
    )
    templates = {
        constants.STEP_PRODUCT: 'core/wizard-step-product.html',
        constants.STEP_PRODUCT_DETAIL: 'core/wizard-step-product-detail.html',
        constants.STEP_CONSUMER_CHANGE: 'core/wizard-step-consumer-change.html',
        constants.STEP_OTHER_CHANGES: 'core/wizard-step-other-information.html',
        constants.STEP_CONSUMER_TYPE: 'core/wizard-step-consumer-type.html',
        constants.STEP_CONSUMER_GROUP: 'core/wizard-step-consumer-group.html',
        constants.STEP_PERSONAL: 'core/wizard-step-personal.html',
        constants.STEP_SUMMARY: 'core/wizard-step-summary-consumer.html',
        constants.STEP_FINISHED: 'core/form-submitted.html',
    }
    summary_template = 'core/summary/report-consumer.html'

    def condition_personal(self):
        cleaned_data = self.get_cleaned_data_for_step(constants.STEP_CONSUMER_TYPE) or {}
        return cleaned_data.get('consumer_type') == constants.INDIVIDUAL_CONSUMER

    def condition_consumer_group(self):
        cleaned_data = self.get_cleaned_data_for_step(constants.STEP_CONSUMER_TYPE) or {}
        return cleaned_data.get('consumer_type') == constants.CONSUMER_GROUP

    condition_dict = {
        constants.STEP_PERSONAL: condition_personal,
        constants.STEP_CONSUMER_GROUP: condition_consumer_group,
    }


class DevelopingCountryWizard(BaseWizard):
    form_list = (
        (constants.STEP_COUNTRY, forms.DevelopingCountryForm),
        (constants.STEP_PRODUCT, forms.ProductSearchForm),
        (constants.STEP_PRODUCT_DETAIL, forms.NoOperationForm),
        (constants.STEP_SALES_VOLUME_BEFORE_BREXIT, forms.SalesVolumeBeforeBrexitForm),
        (constants.STEP_SALES_REVENUE_BEFORE_BREXIT, forms.SalesRevenueBeforeBrexitForm),
        (constants.STEP_SALES_AFTER_BREXIT, forms.ExportsAfterBrexitForm),
        (constants.STEP_MARKET_SIZE_AFTER_BREXIT, forms.ExportMarketSizeAfterBrexitForm),
        (constants.STEP_OTHER_CHANGES, forms.OtherChangesAfterBrexitForm),
        (constants.STEP_OUTCOME, forms.OutcomeForm),
        (constants.STEP_BUSINESS, forms.BusinessDetailsDevelopingCountryForm),
        (constants.STEP_PERSONAL, forms.PersonalDetailsForm),
        (constants.STEP_SUMMARY, forms.SummaryForm),

    )
    templates = {
        constants.STEP_COUNTRY: 'core/wizard-step-developing-country.html',
        constants.STEP_PRODUCT: 'core/wizard-step-product.html',
        constants.STEP_PRODUCT_DETAIL: 'core/wizard-step-product-detail.html',
        constants.STEP_SALES_VOLUME_BEFORE_BREXIT: 'core/wizard-step-sales-export-volume-before-brexit.html',
        constants.STEP_SALES_REVENUE_BEFORE_BREXIT: 'core/wizard-step-export-sales-revenue-before-brexit.html',
        constants.STEP_SALES_AFTER_BREXIT: 'core/wizard-step-export-sales-after-brexit.html',
        constants.STEP_MARKET_SIZE_AFTER_BREXIT: 'core/wizard-step-uk-export-market-size-after-brexit.html',
        constants.STEP_OTHER_CHANGES: 'core/wizard-step-other-changes-after-brexit.html',
        constants.STEP_OUTCOME: 'core/wizard-step-outcome.html',
        constants.STEP_BUSINESS: 'core/wizard-step-importer.html',
        constants.STEP_PERSONAL: 'core/wizard-step-personal.html',
        constants.STEP_SUMMARY: 'core/wizard-step-summary-developing-country.html',
        constants.STEP_FINISHED: 'core/form-submitted.html',
    }
    summary_template = 'core/summary/report-developing-country.html'


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


class SaveForLaterFormView(FormView):
    form_class = forms.SaveForLaterForm
    template_name = 'core/save-for-later.html'
    success_template_name = 'core/save-for-later-success.html'
    success_url = reverse_lazy('landing-page')

    @property
    def return_url(self):
        default_url = reverse('user-type-routing', kwargs={'step': constants.STEP_USER_TYPE})
        return unquote(self.request.GET.get('return_url', '')) or default_url

    def dispatch(self, request, *args, **kwargs):
        if not helpers.get_user_cache_key(request):
            return redirect(self.success_url)
        return super().dispatch(request, *args, **kwargs)

    def get_initial(self):
        initial = super().get_initial()
        url = self.request.build_absolute_uri(self.return_url)
        key = helpers.get_user_cache_key(self.request)
        initial['url'] = f'{url}?key={key}'
        delta = datetime.timedelta(0, settings. SAVE_FOR_LATER_EXPIRES_SECONDS)
        initial['expiry_timestamp'] = (timezone.now() + delta).strftime('%d %B %Y %I:%M %p')
        return initial

    def form_valid(self, form):
        response = form.save(
            template_id=settings.GOV_NOTIFY_TEMPLATE_SAVE_FOR_LATER,
            email_address=form.cleaned_data['email'],
            form_url=self.request.get_full_path(),
            email_reply_to_id=settings.NO_REPLY_NOTIFICATION_SERVICE_UUID
        )
        response.raise_for_status()
        return TemplateResponse(self.request, self.success_template_name, self.get_context_data())

    def get_context_data(self, **kwargs):
        return super().get_context_data(return_url=self.return_url)
