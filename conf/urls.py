import directory_components.views
from directory_components.decorators import skip_ga360

# import directory_healthcheck.views

from django.conf import settings
from django.conf.urls import include, url
from django.contrib.sitemaps.views import sitemap
from django.urls import reverse_lazy
from django.views.generic import RedirectView, TemplateView


import core.views


# sitemaps = {
#     'static': core.views.StaticViewSitemap,
# }


# healthcheck_urls = [
#     url(
#         r'^$',
#         skip_ga360(directory_healthcheck.views.HealthcheckView.as_view()),
#         name='healthcheck'
#     ),
#     url(
#         r'^ping/$',
#         skip_ga360(directory_healthcheck.views.PingView.as_view()),
#         name='ping'
#     ),
# ]


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
