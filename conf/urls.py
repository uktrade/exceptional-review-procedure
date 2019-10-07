from directory_components.decorators import skip_ga360

from django.conf.urls import url
from django.views.generic import TemplateView

import core.views


FINISHED = 'finished'


urlpatterns = [
    url(
        r'^$',
        skip_ga360(core.views.LandingPage.as_view()),
        name='landing-page'
    ),
    url(
        r'^triage/$',
        core.views.RoutingFormView.as_view(),
        name='user-type-routing'
    ),
    url(
        r'^triage/business/(?P<step>.+)/$',
        skip_ga360(core.views.BusinessWizard.as_view(url_name='wizard-business', done_step_name=FINISHED)),
        name='wizard-business'
    ),
    url(
        r'^triage/consumer/(?P<step>.+)/$',
        skip_ga360(core.views.ConsumerWizard.as_view(url_name='wizard-consumer', done_step_name=FINISHED)),
        name='wizard-consumer'
    ),
    url(
        r'^triage/developing-country-business/(?P<step>.+)/$',
        skip_ga360(core.views.DevelopingCountryWizard.as_view(url_name='wizard-developing', done_step_name=FINISHED)),
        name='wizard-developing'
    ),
    url(
        r'^submitted/$',
        skip_ga360(TemplateView.as_view(template_name='core/form-submitted.html')),
        name='submitted'
    ),
    url(
        r'^api/search-companies-house/$',
        core.views.CompaniesHouseSearchAPIView.as_view(),
        name='companies-house-search'
    ),
    url(
        r'^api/search-commodity/$',
        core.views.CommodityCodeSearchAPIView.as_view(),
        name='commodity-search'
    ),
    url(
        r'^save-for-later/$',
        core.views.SaveForLaterFormView.as_view(),
        name='save-for-later'
    ),
]
