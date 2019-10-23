from directory_components.decorators import skip_ga360

from django.conf.urls import url

import core.views
from core import constants
from core.decorators import holding_page_redirect


FINISHED = constants.STEP_FINISHED


urlpatterns = [
    url(
        r'^$',
        skip_ga360(core.views.LandingPageView.as_view()),
        name='landing-page'
    ),
    url(
        r'^privacy-policy/$',
        holding_page_redirect(skip_ga360(core.views.PrivacyPolicyView.as_view())),
        name='privacy-policy'
    ),
    url(
        r'^cookies/$',
        skip_ga360(core.views.CookiesView.as_view()),
        name='cookies'
    ),
    url(
        r'^triage/(?P<step>.+)/$',
        holding_page_redirect(core.views.RoutingWizardView.as_view(url_name='user-type-routing', done_step_name=FINISHED)),
        name='user-type-routing'
    ),
    url(
        r'^business/(?P<step>.+)/$',
        holding_page_redirect(skip_ga360(core.views.BusinessWizard.as_view(url_name='wizard-business', done_step_name=FINISHED))),
        name='wizard-business'
    ),
    url(
        r'^importer/(?P<step>.+)/$',
        holding_page_redirect(skip_ga360(core.views.ImporterWizard.as_view(url_name='wizard-importer', done_step_name=FINISHED))),
        name='wizard-importer'
    ),
    url(
        r'^consumer/(?P<step>.+)/$',
        holding_page_redirect(skip_ga360(core.views.ConsumerWizard.as_view(url_name='wizard-consumer', done_step_name=FINISHED))),
        name='wizard-consumer'
    ),
    url(
        r'^developing-country-business/(?P<step>.+)/$',
        holding_page_redirect(skip_ga360(core.views.DevelopingCountryWizard.as_view(url_name='wizard-developing', done_step_name=FINISHED))),
        name='wizard-developing'
    ),
    url(
        r'^api/search-companies-house/$',
        holding_page_redirect(core.views.CompaniesHouseSearchAPIView.as_view()),
        name='companies-house-search'
    ),
    url(
        r'^save-for-later/$',
        holding_page_redirect(core.views.SaveForLaterFormView.as_view()),
        name='save-for-later'
    ),
]
