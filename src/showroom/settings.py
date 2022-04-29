"""Django settings for showroom project.

Generated by 'django-admin startproject' using Django 2.2.

For more information on this file, see
https://docs.djangoproject.com/en/2.2/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/2.2/ref/settings/

Before deployment please see
https://docs.djangoproject.com/en/2.2/howto/deployment/checklist/
"""

import os
import sys
from email.utils import getaddresses
from urllib.parse import urlparse

import environ

from django.core.exceptions import ImproperlyConfigured
from django.urls import reverse_lazy
from django.utils.translation import ugettext_lazy as _

env = environ.Env()
env.read_env()

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

PROJECT_NAME = '.'.join(__name__.split('.')[:-1])

try:
    from .secret_key import SECRET_KEY
except ImportError:
    from django.core.management.utils import get_random_secret_key

    with open(os.path.join(BASE_DIR, PROJECT_NAME, 'secret_key.py'), 'w+') as f:
        SECRET_KEY = get_random_secret_key()
        f.write("SECRET_KEY = '%s'\n" % SECRET_KEY)

# Introduced in Django 3.2, we can explicitly set a field for auto-created primary keys
# Therefore we want to stick with the old AutoField. In the future a migration to the
# newer BigAutoField (which is now standard) is advisable. (TODO)
DEFAULT_AUTO_FIELD = 'django.db.models.AutoField'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = env.bool('DEBUG', default=False)

# Detect if executed under test
TESTING = any(
    test in sys.argv
    for test in (
        'test',
        'csslint',
        'jenkins',
        'jslint',
        'jtest',
        'lettuce',
        'pep8',
        'pyflakes',
        'pylint',
        'sloccount',
    )
)

DOCKER = env.bool('DOCKER', default=True)

SITE_URL = env.str('SITE_URL')

FORCE_SCRIPT_NAME = env.str('FORCE_SCRIPT_NAME', default='/showroom')

ALLOWED_HOSTS = env.list('ALLOWED_HOSTS', default=[urlparse(SITE_URL).hostname])

BEHIND_PROXY = env.bool('BEHIND_PROXY', default=True)

DJANGO_ADMINS = env('DJANGO_ADMINS', default=None)

if DJANGO_ADMINS:
    ADMINS = getaddresses([DJANGO_ADMINS])
    MANAGERS = ADMINS

SUPERUSERS = env.tuple('DJANGO_SUPERUSERS', default=())


# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    # Third-party apps
    'django_cas_ng',
    'django_extensions',
    'rest_framework',
    'drf_spectacular',
    'django_rq',
    'corsheaders',
    # Project apps
    'core',
    'general',
    'api',
    'user_preferences',
]

AUTHENTICATION_BACKENDS = [
    'django.contrib.auth.backends.ModelBackend',
    'django_cas_ng.backends.CASBackend',
]

LOGIN_URL = reverse_lazy('cas_ng_login')
LOGOUT_URL = reverse_lazy('cas_ng_logout')

CAS_SERVER_URL = env.str('CAS_SERVER', default=f'{SITE_URL}cas/')
CAS_LOGIN_MSG = None
CAS_LOGGED_MSG = None
CAS_RENEW = False
CAS_LOGOUT_COMPLETELY = True
CAS_RETRY_LOGIN = True
CAS_VERSION = '3'
CAS_APPLY_ATTRIBUTES_TO_USER = True
CAS_REDIRECT_URL = env.str('CAS_REDIRECT_URL', default=FORCE_SCRIPT_NAME or '/')

DISABLE_USER_REPO = env.bool('DISABLE_USER_REPO', default=False)
DEFAULT_USER_REPO = env.int('DEFAULT_USER_REPO', default=None)

USER_PREFERENCES_API_BASE = env.str(
    'USER_PREFERENCES_API_BASE', default=f'{CAS_SERVER_URL}api/v1/'
)
USER_PREFERENCES_API_KEY = env.str('USER_PREFERENCES_API_KEY', default=None)
USER_REPO_CACHE_TIME = env.int('USER_REPO_CACHE_TIME', default=15)

SKOSMOS_API = env.str(
    'SKOSMOS_API', default='https://voc.uni-ak.ac.at/skosmos/rest/v1/'
)
TAX_ID = 'potax'
TAX_GRAPH = 'http://base.uni-ak.ac.at/portfolio/taxonomy/'
VOC_ID = 'povoc'
VOC_GRAPH = 'http://base.uni-ak.ac.at/portfolio/vocabulary/'
ACTIVE_SCHEMAS = env.list(
    'ACTIVE_SCHEMAS',
    default=[
        'architecture',
        'audio',
        'awards_and_grants',
        'concert',
        'conference',
        'conference_contribution',
        'design',
        'document_publication',
        'event',
        'exhibition',
        'fellowship_visiting_affiliation',
        'festival',
        'image',
        'performance',
        'research_project',
        'sculpture',
        'software',
        'film_video',
    ],
)

# The default limit for searches, when no limit parameter is provided
SEARCH_LIMIT = env.int('SEARCH_LIMIT', default=100)

# Time span (in days) into the future and past for the current_activities filter
# TODO: deprecated - remove once old model search functions are removed
CURRENT_ACTIVITIES_FUTURE = env.int('CURRENT_ACTIVITIES_FUTURE', default=90)
CURRENT_ACTIVITIES_PAST = env.int('CURRENT_ACTIVITIES_PAST', default=365)

# Factor by which past dates are multiplied for currentness search
CURRENTNESS_PAST_WEIGHT = env.int('CURRENTNESS_PAST_WEIGHT', default=4)

# The default showcase to be used for the initial endpoint, if the requested entity's
# showcase is empty. Also check for syntactical validity.
DEFAULT_SHOWCASE = [x.split(':') for x in env.list('DEFAULT_SHOWCASE', default=[])]
for x in DEFAULT_SHOWCASE:
    if type(x) != list or len(x) != 2:
        raise ImproperlyConfigured(
            'Syntax error in DEFAULT_SHOWCASE environment variable'
        )
    if not x[0] or not x[1]:
        raise ImproperlyConfigured(
            'Syntax error in DEFAULT_SHOWCASE environment variable'
        )

DEFAULT_ENTITY = env.str('DEFAULT_ENTITY', default=None)

SHOWCASE_DEMO_USERS = env.list('SHOWCASE_DEMO_USERS', default=[])
SHOWCASE_DEMO_ENTITY_EDITING = env.list('SHOWCASE_DEMO_ENTITY_EDITING', default=[])

""" Email settings """
SERVER_EMAIL = 'error@%s' % urlparse(SITE_URL).hostname

EMAIL_HOST_USER = env.str('EMAIL_HOST_USER', default='')
EMAIL_HOST_PASSWORD = env.str('EMAIL_HOST_PASSWORD', default='')
EMAIL_HOST = env.str('EMAIL_HOST', default='localhost')
EMAIL_PORT = env.int('EMAIL_PORT', default=25)
EMAIL_USE_TLS = env.bool('EMAIL_USE_TLS', default=False)
EMAIL_USE_LOCALTIME = env.bool('EMAIL_USE_LOCALTIME', default=True)

EMAIL_SUBJECT_PREFIX = '{} '.format(
    env.str('EMAIL_SUBJECT_PREFIX', default='[showroom]').strip()
)
if DEBUG:
    EMAIL_BACKEND = 'django.core.mail.backends.filebased.EmailBackend'
    EMAIL_FILE_PATH = os.path.join(BASE_DIR, '..', 'tmp', 'emails')

    if not os.path.exists(EMAIL_FILE_PATH):
        os.makedirs(EMAIL_FILE_PATH)

""" Https settings """
if SITE_URL.startswith('https'):
    CSRF_COOKIE_SECURE = True
    SESSION_COOKIE_SECURE = True
    SECURE_SSL_REDIRECT = True
    SECURE_HSTS_SECONDS = 31536000

X_FRAME_OPTIONS = 'DENY'

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.locale.LocaleMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

if BEHIND_PROXY:
    MIDDLEWARE += [
        'general.middleware.SetRemoteAddrFromForwardedFor',
    ]
    USE_X_FORWARDED_HOST = True
    SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')

ROOT_URLCONF = f'{PROJECT_NAME}.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
            'debug': DEBUG,
            'string_if_invalid': "[invalid variable '%s'!]" if DEBUG else '',
        },
    },
]

WSGI_APPLICATION = f'{PROJECT_NAME}.wsgi.application'


# Database
# https://docs.djangoproject.com/en/2.2/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql_psycopg2',
        'NAME': os.environ.get('POSTGRES_DB', f'django_{PROJECT_NAME}'),
        'USER': os.environ.get('POSTGRES_USER', f'django_{PROJECT_NAME}'),
        'PASSWORD': os.environ.get('POSTGRES_PASSWORD', f'password_{PROJECT_NAME}'),
        'HOST': f'{PROJECT_NAME}-postgres' if DOCKER else 'localhost',
        'PORT': os.environ.get('POSTGRES_PORT', '5432'),
    }
}


# Password validation
# https://docs.djangoproject.com/en/2.2/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]


# Internationalization
# https://docs.djangoproject.com/en/2.2/topics/i18n/

LANGUAGE_CODE = 'en'
TIME_ZONE = 'Europe/Vienna'
USE_I18N = True
USE_L10N = True
USE_TZ = True

LANGUAGES = (
    ('de', _('German')),
    ('en', _('English')),
)

LANGUAGES_DICT = dict(LANGUAGES)

LOCALES = {
    'de': 'de_DE',
    'en': 'en_GB',
}

DATETIME_FORMATS = {
    'de': 'dd. MMMM y, HH:mm',
    'en': 'dd MMMM y, HH:mm',
}

DATE_FORMATS = {
    'de': 'dd.MM.y',
    'en': 'dd/MM/y',
}

TIME_FORMATS = {
    'de': 'HH:mm',
    'en': 'HH:mm',
}

LOCALE_PATHS = [
    os.path.join(BASE_DIR, 'locale'),
]

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/2.2/howto/static-files/

STATICFILES_DIRS = (
    '{}{}'.format(os.path.normpath(os.path.join(BASE_DIR, 'static')), os.sep),
)
STATIC_URL = '{}/s/'.format(FORCE_SCRIPT_NAME if FORCE_SCRIPT_NAME else '')
STATIC_ROOT = '{}{}'.format(
    os.path.normpath(os.path.join(BASE_DIR, 'assets', 'static')), os.sep
)

MEDIA_URL = '{}/m/'.format(FORCE_SCRIPT_NAME if FORCE_SCRIPT_NAME else '')
MEDIA_ROOT = '{}{}'.format(
    os.path.normpath(os.path.join(BASE_DIR, 'assets', 'media')), os.sep
)

FILE_UPLOAD_PERMISSIONS = 0o644

""" Logging """
LOG_DIR = os.path.join(BASE_DIR, '..', 'logs')

if not os.path.exists(LOG_DIR):
    os.makedirs(LOG_DIR)

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '%(levelname)s %(asctime)s %(module)s %(process)d %(thread)d %(message)s'
        },
        'simple': {'format': '%(levelname)s %(message)s'},
        'simple_with_time': {
            'format': '%(levelname)s %(asctime)s %(message)s',
        },
    },
    'handlers': {
        'null': {
            'level': 'DEBUG',
            'class': 'logging.NullHandler',
        },
        'console': {
            'level': 'DEBUG',
            'class': 'logging.StreamHandler',
            'formatter': 'simple',
        },
        'file': {
            'level': 'DEBUG',
            'class': 'concurrent_log_handler.ConcurrentRotatingFileHandler',
            'filename': os.path.join(LOG_DIR, 'application.log'),
            'maxBytes': 1024 * 1024 * 5,  # 5 MB
            'backupCount': 1000,
            'use_gzip': True,
            'delay': True,
            'formatter': 'verbose',
        },
        'mail_admins': {
            'level': 'ERROR',
            'class': 'django.utils.log.AdminEmailHandler',
        },
        'stream_to_console': {
            'level': 'DEBUG',
            'class': 'logging.StreamHandler',
        },
        'rq_console': {
            'level': 'DEBUG',
            'class': 'logging.StreamHandler',
            'formatter': 'simple_with_time',
        },
    },
    'loggers': {
        '': {
            'handlers': ['console', 'file', 'mail_admins'],
            'propagate': True,
            'level': 'INFO',
        },
        'django': {
            'handlers': ['console', 'file', 'mail_admins'],
            'propagate': True,
            'level': 'INFO',
        },
        'django.request': {
            'handlers': ['console', 'file', 'mail_admins'],
            'level': 'ERROR',
            'propagate': True,
        },
        'rq.worker': {
            'handlers': ['rq_console', 'mail_admins'],
            'level': 'DEBUG',
            'propagate': False,
        },
    },
}

""" Cache settings """
CACHES = {
    'default': {
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': 'redis://{}:{}/0'.format(
            f'{PROJECT_NAME}-redis' if DOCKER else 'localhost',
            env.int('REDIS_PORT', default=6379),
        ),
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
        },
    }
}


""" RQ worker settings """
RQ_QUEUES = {
    'default': {'USE_REDIS_CACHE': 'default', 'DEFAULT_TIMEOUT': 500},
    'high': {'USE_REDIS_CACHE': 'default', 'DEFAULT_TIMEOUT': 14400},
}

if DEBUG or TESTING:
    for queueConfig in iter(RQ_QUEUES.values()):
        queueConfig['ASYNC'] = False

RQ_EXCEPTION_HANDLERS = ['general.rq.handlers.exception_handler']

RQ_FAILURE_TTL = 2628288  # approx. 3 month

WORKER_DELAY_ENTITY = env.int('WORKER_DELAY_ENTITY', default=10)


""" Session settings """
SESSION_ENGINE = 'django.contrib.sessions.backends.cache'
SESSION_CACHE_ALIAS = 'default'
SESSION_COOKIE_NAME = f'sessionid_{PROJECT_NAME}'
SESSION_COOKIE_DOMAIN = env.str('SESSION_COOKIE_DOMAIN', default=None)
SESSION_EXPIRE_AT_BROWSER_CLOSE = True

CSRF_COOKIE_NAME = f'csrftoken_{PROJECT_NAME}'
CSRF_COOKIE_DOMAIN = env.str('CSRF_COOKIE_DOMAIN', default=None)
CSRF_TRUSTED_ORIGINS = env.list('CSRF_TRUSTED_ORIGINS', default=[])

CORS_ALLOW_CREDENTIALS = env.bool('CORS_ALLOW_CREDENTIALS', default=False)
CORS_ORIGIN_ALLOW_ALL = env.bool('CORS_ORIGIN_ALLOW_ALL', default=False)
CORS_ORIGIN_WHITELIST = env.list('CORS_ORIGIN_WHITELIST', default=[])
# CORS_URLS_REGEX = r'^/()/.*$'

REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework.authentication.SessionAuthentication',
    ),
    'DEFAULT_PERMISSION_CLASSES': [],
    'DEFAULT_RENDERER_CLASSES': (
        'rest_framework.renderers.JSONRenderer',
        # 'rest_framework.renderers.BrowsableAPIRenderer',
    ),
    'DEFAULT_VERSIONING_CLASS': 'rest_framework.versioning.URLPathVersioning',
    'DEFAULT_VERSION': 'v1',
    'ORDERING_PARAM': 'sort',
    'DEFAULT_SCHEMA_CLASS': 'drf_spectacular.openapi.AutoSchema',
}

# spectacular settings
# https://drf-spectacular.readthedocs.io/en/latest/settings.html
SPECTACULAR_SETTINGS = {
    'TITLE': 'Showroom API v1',
    'VERSION': '1.0.0',
    'DESCRIPTION': """Provides public access to all activities published to *Showroom*, as well as authenticated access
    for users and repositories to publish and update activites, create and maintain albums. For a general project
    description visit the [Portfolio/Showroom website](https://portfolio-showroom.ac.at), for the sources and
    documentation of this component go to **TODO:insertlinktogithubrepo**.
    """,
    'TAGS': ['public', 'auth', 'repo', 'api'],
    'SERVERS': [
        {
            'url': env.str(
                'OPENAPI_SERVER_URL',
                default=f'{SITE_URL.rstrip("/")}{FORCE_SCRIPT_NAME}',
            ),
            'description': env.str('OPENAPI_SERVER_DESCRIPTION', default='Showroom'),
        },
    ],
    # available SwaggerUI configuration parameters
    # https://swagger.io/docs/open-source-tools/swagger-ui/usage/configuration/
    'SWAGGER_UI_SETTINGS': {
        'deepLinking': True,
        'persistAuthorization': True,
        'displayOperationId': True,
    },
    # available SwaggerUI versions: https://github.com/swagger-api/swagger-ui/releases
    'SWAGGER_UI_DIST': '//unpkg.com/swagger-ui-dist@3.35.1',  # default
    # "SWAGGER_UI_FAVICON_HREF": settings.STATIC_URL + "your_company_favicon.png",  # default is swagger favicon
    'ENUM_NAME_OVERRIDES': {
        'ShowroomObjectTypeEnum': (
            ('act', 'activity'),
            ('alb', 'album'),
            ('per', 'person'),
            ('ins', 'institution'),
            ('dep', 'department'),
        ),
        'MediaTypeEnum': (
            ('i', 'Image'),
            ('a', 'Audio'),
            ('v', 'Video'),
            ('d', 'Document'),
            ('x', 'Undefined'),
        ),
    },
}


if DEBUG:
    INSTALLED_APPS += ['debug_toolbar']
    MIDDLEWARE.insert(
        MIDDLEWARE.index('django.contrib.sessions.middleware.SessionMiddleware'),
        'debug_toolbar.middleware.DebugToolbarMiddleware',
    )
    INTERNAL_IPS = ('127.0.0.1',)
