from directory_components.decorators import skip_ga360

from django.conf.urls import url
from django.urls import reverse_lazy
from django.views.generic import RedirectView

import core.views
from core import constants
from conf import settings


FINISHED = constants.STEP_FINISHED


urlpatterns = [
    url(
        r'^cookies/$',
        skip_ga360(core.views.CookiesView.as_view()),
        name='cookies'
    ),
    url(
        r'^privacy-policy/$',
        skip_ga360(core.views.PrivacyPolicyView.as_view()),
        name='privacy-policy'
    ),
    url(
        r'^accessibility-statement/$',
        skip_ga360(core.views.AccessibilityStatementView.as_view()),
        name='accessibility-statement'
    ),
]

service_urls = [
    url(
        r'^triage/(?P<step>.+)/$',
        core.views.RoutingWizardView.as_view(url_name='user-type-routing', done_step_name=FINISHED),
        name='user-type-routing'
    ),
    url(
        r'^business/(?P<step>.+)/$',
        skip_ga360(core.views.BusinessWizard.as_view(url_name='wizard-business', done_step_name=FINISHED)),
        name='wizard-business'
    ),
    url(
        r'^importer/(?P<step>.+)/$',
        skip_ga360(core.views.ImporterWizard.as_view(url_name='wizard-importer', done_step_name=FINISHED)),
        name='wizard-importer'
    ),
    url(
        r'^consumer/(?P<step>.+)/$',
        skip_ga360(core.views.ConsumerWizard.as_view(url_name='wizard-consumer', done_step_name=FINISHED)),
        name='wizard-consumer'
    ),
    url(
        r'^developing-country-business/(?P<step>.+)/$',
        skip_ga360(core.views.DevelopingCountryWizard.as_view(url_name='wizard-developing', done_step_name=FINISHED)),
        name='wizard-developing'
    ),
    url(
        r'^api/search-companies-house/$',
        core.views.CompaniesHouseSearchAPIView.as_view(),
        name='companies-house-search'
    ),
    url(
        r'^save-for-later/$',
        core.views.SaveForLaterFormView.as_view(),
        name='save-for-later'
    ),
]

if settings.FEATURE_FLAGS['SERVICE_HOLDING_PAGE_ON']:
    urlpatterns += [
        url(
            r'^$',
            core.views.ServiceHoldingPageView.as_view(),
            name='landing-page',
        ),
    ]
else:
    urlpatterns += service_urls
    urlpatterns += [
        url(
            r'^$',
            RedirectView.as_view(url=reverse_lazy('user-type-routing', kwargs={'step': constants.STEP_USER_TYPE})),
            name='landing-page',
        ),
    ]
