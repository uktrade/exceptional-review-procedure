from directory_components.decorators import skip_ga360

from django.conf.urls import url

import core.views
from core import constants


FINISHED = constants.STEP_FINISHED


urlpatterns = [
    url(
        r'^$',
        skip_ga360(core.views.LandingPage.as_view()),
        name='landing-page'
    ),
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
