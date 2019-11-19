import os

import environ

import directory_healthcheck.backends

from datetime import datetime


env = environ.Env()
for env_file in env.list('ENV_FILES', default=[]):
    env.read_env(f'conf/env/{env_file}')

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)

PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
BASE_DIR = os.path.dirname(PROJECT_ROOT)

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = env.str('SECRET_KEY')

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = env.bool('DEBUG', False)

# As the app is running behind a host-based router supplied by Heroku or other
# PaaS, we can open ALLOWED_HOSTS
ALLOWED_HOSTS = ['*']


# Application definition

INSTALLED_APPS = [
    'django.contrib.staticfiles',
    'django.contrib.humanize',
    'django.contrib.messages',
    'django.contrib.auth',
    'django.contrib.contenttypes',  # required by DRF, not using DB
    'raven.contrib.django.raven_compat',
    'django.contrib.sessions',
    'django.contrib.sitemaps',
    'captcha',
    'directory_components',
    'health_check.cache',
    'directory_healthcheck',
    'core',
]

MIDDLEWARE = [
    'directory_components.middleware.MaintenanceModeMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.common.CommonMiddleware',
]

ROOT_URLCONF = 'conf.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.template.context_processors.i18n',
                'django.contrib.messages.context_processors.messages',
                'directory_components.context_processors.analytics',
                'directory_components.context_processors.cookie_notice',
                'directory_components.context_processors.feature_flags',
            ],
        },
    },
]

WSGI_APPLICATION = 'conf.wsgi.application'

VCAP_SERVICES = env.json('VCAP_SERVICES', {})

if 'redis' in VCAP_SERVICES:
    REDIS_URL = VCAP_SERVICES['redis'][0]['credentials']['uri']
else:
    REDIS_URL = env.str('REDIS_URL', '')

if REDIS_URL:
    cache = {
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': REDIS_URL,
        'OPTIONS': {
            'CLIENT_CLASS': "django_redis.client.DefaultClient",
        }
    }
else:
    cache = {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
        'LOCATION': 'unique-snowflake',
    }


CACHES = {
    'default': cache,
    'cms_fallback': cache,
    'api_fallback': cache
}

# Internationalization
# https://docs.djangoproject.com/en/1.9/topics/i18n/
LANGUAGE_CODE = 'en-gb'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_L10N = True
USE_TZ = True

# https://docs.djangoproject.com/en/2.2/ref/settings/#std:setting-LANGUAGE_COOKIE_NAME
LANGUAGE_COOKIE_NAME = env.str('LANGUAGE_COOKIE_NAME', 'django_language')
# Django's default value for LANGUAGE_COOKIE_DOMAIN is None
LANGUAGE_COOKIE_DOMAIN = env.str('LANGUAGE_COOKIE_DOMAIN', None)

# needed only for dev local storage
MEDIA_ROOT = os.path.join(PROJECT_ROOT, 'media')
MEDIA_URL = '/media/'

# Static files served with Whitenoise and AWS Cloudfront
# http://whitenoise.evans.io/en/stable/django.html#instructions-for-amazon-cloudfront
# http://whitenoise.evans.io/en/stable/django.html#restricting-cloudfront-to-static-files
STATIC_ROOT = os.path.join(PROJECT_ROOT, 'staticfiles')
STATIC_HOST = env.str('STATIC_HOST', '')
STATIC_URL = STATIC_HOST + '/static/'
STATICFILES_STORAGE = env.str(
    'STATICFILES_STORAGE',
    'whitenoise.storage.CompressedManifestStaticFilesStorage'
)

# Logging for development
if DEBUG:
    LOGGING = {
        'version': 1,
        'disable_existing_loggers': False,
        'filters': {
            'require_debug_false': {
                '()': 'django.utils.log.RequireDebugFalse'
            }
        },
        'handlers': {
            'console': {
                'level': 'DEBUG',
                'class': 'logging.StreamHandler',
            },
        },
        'loggers': {
            'django.request': {
                'handlers': ['console'],
                'level': 'ERROR',
                'propagate': True,
            },
            '': {
                'handlers': ['console'],
                'level': 'DEBUG',
                'propagate': False,
            },
        }
    }
else:
    # Sentry logging
    LOGGING = {
        'version': 1,
        'disable_existing_loggers': False,
        'root': {
            'level': 'WARNING',
            'handlers': ['sentry'],
        },
        'formatters': {
            'verbose': {
                'format': '%(levelname)s %(asctime)s %(module)s '
                          '%(process)d %(thread)d %(message)s'
            },
        },
        'handlers': {
            'sentry': {
                'level': 'ERROR',
                'class': (
                    'raven.contrib.django.raven_compat.handlers.SentryHandler'
                ),
                'tags': {'custom-tag': 'x'},
            },
            'console': {
                'level': 'DEBUG',
                'class': 'logging.StreamHandler',
                'formatter': 'verbose'
            }
        },
        'loggers': {
            'raven': {
                'level': 'DEBUG',
                'handlers': ['console'],
                'propagate': False,
            },
            'sentry.errors': {
                'level': 'DEBUG',
                'handlers': ['console'],
                'propagate': False,
            },
        },
    }


SECURE_SSL_REDIRECT = env.bool('SECURE_SSL_REDIRECT', True)
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
USE_X_FORWARDED_HOST = True
SECURE_HSTS_SECONDS = env.int('SECURE_HSTS_SECONDS', 16070400)
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
X_FRAME_OPTIONS = 'DENY'
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
LANGUAGE_COOKIE_SECURE = env.bool('LANGUAGE_COOKIE_SECURE', True)
COUNTRY_COOKIE_SECURE = env.bool('COUNTRY_COOKIE_SECURE', True)

# Sentry
RAVEN_CONFIG = {
    'dsn': env.str('SENTRY_DSN', ''),
    'processors': (
        'raven.processors.SanitizePasswordsProcessor',
    )
}

SESSION_ENGINE = 'django.contrib.sessions.backends.signed_cookies'
SESSION_COOKIE_SECURE = env.bool('SESSION_COOKIE_SECURE', True)
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_NAME = env.str('SESSION_COOKIE_NAME', 'erp_session_id')
MESSAGE_STORAGE = 'django.contrib.messages.storage.session.SessionStorage'

CSRF_COOKIE_SECURE = env.bool('CSRF_COOKIE_SECURE', True)
CSRF_COOKIE_HTTPONLY = True

# Google Recaptcha
RECAPTCHA_PUBLIC_KEY = env.str('RECAPTCHA_PUBLIC_KEY')
RECAPTCHA_PRIVATE_KEY = env.str('RECAPTCHA_PRIVATE_KEY')
# NOCAPTCHA = True turns on version 2 of recaptcha
NOCAPTCHA = env.bool('NOCAPTCHA', True)

# Google tag manager
GOOGLE_TAG_MANAGER_ID = env.str('GOOGLE_TAG_MANAGER_ID', '')
GOOGLE_TAG_MANAGER_ENV = env.str('GOOGLE_TAG_MANAGER_ENV', '')
UTM_COOKIE_DOMAIN = None
PRIVACY_COOKIE_DOMAIN = env.str('PRIVACY_COOKIE_DOMAIN', '')

# django-storages for thumbnails
AWS_STORAGE_BUCKET_NAME = env.str('AWS_STORAGE_BUCKET_NAME', '')
AWS_DEFAULT_ACL = 'public-read'
AWS_AUTO_CREATE_BUCKET = True
AWS_QUERYSTRING_AUTH = False
AWS_S3_ENCRYPTION = False
AWS_S3_FILE_OVERWRITE = False
AWS_S3_CUSTOM_DOMAIN = env.str('AWS_S3_CUSTOM_DOMAIN', '')
AWS_S3_REGION_NAME = env.str('AWS_S3_REGION_NAME', 'eu-west-1')
AWS_S3_URL_PROTOCOL = env.str('AWS_S3_URL_PROTOCOL', 'https:')
# Needed for new AWS regions
# https://github.com/jschneier/django-storages/issues/203
AWS_S3_SIGNATURE_VERSION = env.str('AWS_S3_SIGNATURE_VERSION', 's3v4')
AWS_QUERYSTRING_AUTH = env.bool('AWS_QUERYSTRING_AUTH', False)
S3_USE_SIGV4 = env.bool('S3_USE_SIGV4', True)
AWS_S3_HOST = env.str('AWS_S3_HOST', 's3.eu-west-1.amazonaws.com')

# feature flags
FEATURE_FLAGS = {
    'SERVICE_OFF': env.bool('FEATURE_SERVICE_DISABLED', True),
    'MAINTENANCE_MODE_ON': env.bool('FEATURE_MAINTENANCE_MODE_ENABLED', False),
    'SERVICE_HOLDING_PAGE_ON': env.bool('FEATURE_SERVICE_HOLDING_PAGE_ENABLED', True),
}

# Directory healthcheck
DIRECTORY_HEALTHCHECK_TOKEN = env.str('HEALTH_CHECK_TOKEN')
DIRECTORY_HEALTHCHECK_BACKENDS = [
    directory_healthcheck.backends.FormsAPIBackend,
    # health_check.cache.CacheBackend is also registered in
    # INSTALLED_APPS's health_check.cache
]

SILENCED_SYSTEM_CHECKS = ['captcha.recaptcha_test_key_error']

# directory forms api client
DIRECTORY_FORMS_API_BASE_URL = env.str('DIRECTORY_FORMS_API_BASE_URL')
DIRECTORY_FORMS_API_API_KEY = env.str('DIRECTORY_FORMS_API_API_KEY')
DIRECTORY_FORMS_API_SENDER_ID = env.str('DIRECTORY_FORMS_API_SENDER_ID')
DIRECTORY_FORMS_API_DEFAULT_TIMEOUT = env.int('DIRECTORY_API_FORMS_DEFAULT_TIMEOUT', 5)
DIRECTORY_FORMS_API_ZENDESK_SEVICE_NAME = env.str('DIRECTORY_FORMS_API_ZENDESK_SEVICE_NAME', 'directory')

# Companies House Search
DIRECTORY_CH_SEARCH_CLIENT_BASE_URL = env.str('DIRECTORY_CH_SEARCH_CLIENT_BASE_URL')
DIRECTORY_CH_SEARCH_CLIENT_API_KEY = env.str('DIRECTORY_CH_SEARCH_CLIENT_API_KEY')
DIRECTORY_CH_SEARCH_CLIENT_SENDER_ID = env.str('DIRECTORY_CH_SEARCH_CLIENT_SENDER_ID', 'directory')
DIRECTORY_CH_SEARCH_CLIENT_DEFAULT_TIMEOUT = env.str('DIRECTORY_CH_SEARCH_CLIENT_DEFAULT_TIMEOUT', 5)

GOV_NOTIFY_TEMPLATE_SAVE_FOR_LATER = env.str(
    'GOV_NOTIFY_TEMPLATE_SAVE_FOR_LATER',
    '16e574f1-b723-445c-b25a-ee7cbacf1a9a'
)

NO_REPLY_NOTIFICATION_SERVICE_UUID = env.str(
    'NO_REPLY_NOTIFICATION_SERVICE_UUID',
    'c071d4f6-94a7-4afd-9acb-6b164737731c'
)

# DIT helpdesk API
DIT_HELPDESK_URL = env.str('DIT_HELPDESK_URL')

SAVE_FOR_LATER_EXPIRES_SECONDS = 60 * 60 * 72  # 72 hours

SERVICE_AVAILABILITY_START_DATE = datetime.strptime(
    env.str('SERVICE_AVAILABILITY_START_DATE', '2019-11-01'), '%Y-%m-%d').date()

SERVICE_AVAILABILITY_END_DATE = datetime.strptime(
    env.str('SERVICE_AVAILABILITY_END_DATE', '2020-04-30'), '%Y-%m-%d').date()

# DIT Zendesk domain
ERP_ZENDESK_SUBDOMAIN = env.str('ERP_ZENDESK_SUBDOMAIN')
