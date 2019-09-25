from directory_components.decorators import skip_ga360

from django.conf.urls import url
from django.urls import reverse_lazy
from django.views.generic import RedirectView, TemplateView

import core.views


urlpatterns = [
    url(
        r'^$',
        skip_ga360(core.views.LandingPage.as_view()),
        name='landing-page'
    ),
    url(
        r'^triage/$',
        RedirectView.as_view(url=reverse_lazy('wizard', kwargs={'step': 'location'}))
    ),
    url(
        r'^triage/(?P<step>.+)/$',
        skip_ga360(core.views.Wizard.as_view(url_name='wizard', done_step_name='finished')),
        name='wizard'
    ),
    url(
        r'^submitted/$',
        skip_ga360(TemplateView.as_view(template_name='core/form-submitted.html')),
        name='submitted'
    ),
    url(
        r'^api/companies-house-search/$',
        core.views.CompaniesHouseSearchAPIView.as_view(),
        name='companies-house-search'
    ),
    url(
        r'^save-for-later/$',
        core.views.SaveForLaterFormView.as_view(),
        name='save-for-later'
    ),
]
