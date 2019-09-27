from directory_ch_client.client import ch_search_api_client
from directory_forms_api_client import actions
from directory_forms_api_client.helpers import FormSessionMixin, Sender
from formtools.wizard.views import NamedUrlSessionWizardView
from rest_framework.generics import GenericAPIView
from rest_framework.response import Response

from django.conf import settings
from django.contrib.messages.views import SuccessMessageMixin
from django.shortcuts import redirect, Http404
from django.urls import reverse, reverse_lazy
from django.views.generic import FormView, TemplateView

from core import forms, helpers, serializers


PRODUCT = 'product-search'
IMPACT = 'impact'
TARIFF_COMMENT = 'tariff-comment'
NON_TARIFF_COMMENT = 'non-tariff-comment'
OUTCOME = 'outcome'
BUSINESS = 'business'
PERSONAL = 'personal'
SUMMARY = 'summary'
TYPE = 'routing'


class LandingPage(TemplateView):
    template_name = 'core/landing-page.html'


class Wizard(FormSessionMixin, NamedUrlSessionWizardView):
    storage_name = 'core.helpers.CacheStorage'
    success_url = reverse_lazy('submitted')
    form_list = (
        (TYPE, forms.LocationRoutingForm),
        (PRODUCT, forms.ProductSearchForm),
        (IMPACT, forms.BusinessChangeForm),
        (TARIFF_COMMENT, forms.TariffRelatedCommentForm),
        (NON_TARIFF_COMMENT, forms.NonTariffRelatedCommentForm),
        (OUTCOME, forms.OutcomeForm),
        (BUSINESS, forms.CompaniesHouseBusinessDetailsForm),
        (PERSONAL, forms.PersonalDetailsForm),
        (SUMMARY, forms.SummaryForm),
    )

    templates = {
        TYPE: 'core/wizard-step-type.html',
        PRODUCT: 'core/wizard-step-product.html',
        IMPACT: 'core/wizard-step-impact.html',
        TARIFF_COMMENT: 'core/wizard-step-tariff-comment.html',
        NON_TARIFF_COMMENT: 'core/wizard-step-non-tariff-comment.html',
        OUTCOME: 'core/wizard-step-outcome.html',
        BUSINESS: 'core/wizard-step-business.html',
        PERSONAL: 'core/wizard-step-personal.html',
        SUMMARY: 'core/wizard-step-summary.html',
    }

    def dispatch(self, request, *args, **kwargs):
        if 'key' in self.request.GET:
            helpers.load_saved_submission(request=request, key=self.request.GET['key'])
        return super().dispatch(request=request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        if request.POST.get('wizard_save_for_later'):
            self.storage.set_step_data(self.steps.current, request.POST)
            self.storage.mark_shared()
            url = reverse('save-for-later')
            return redirect(f'{url}?step={self.steps.current}')
        return super().post(request=request, *args, **kwargs)

    def get_template_names(self):
        return [self.templates[self.steps.current]]

    def get_context_data(self, form, **kwargs):
        context = super().get_context_data(form=form, **kwargs)
        if self.steps.current == SUMMARY:
            context['all_cleaned_data'] = self.get_all_cleaned_data()
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
            form_url=reverse('wizard', kwargs={'step': TYPE}),
            form_session=self.form_session,
            sender=sender,
        )
        response = action.save(form_data)
        response.raise_for_status()
        return redirect(self.success_url)

    def serialize_form_list(self, form_list):
        data = {}
        for form in form_list:
            data.update(form.cleaned_data)
        del data['terms_agreed']
        del data['captcha']
        return data


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
        results = [
            {
                'text': result['description'],
                'value': result['commodity_code'],
            }
            for result in response.json()['results']
        ]
        return Response(results)


class SaveForLaterFormView(SuccessMessageMixin, FormView):
    form_class = forms.SaveForLaterForm
    template_name = 'core/save-for-later.html'
    success_url = reverse_lazy('landing-page')
    success_message = 'Response saved. Check your emails.'

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        url = self.request.build_absolute_uri(reverse('wizard', kwargs={'step': self.request.GET.get('step', TYPE)}))
        user_cache_key = helpers.get_user_cache_key(self.request)
        if not user_cache_key:
            raise Http404()
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
