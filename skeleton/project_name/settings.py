"""
Django settings for skeleton project.

For more information on this file, see
https://docs.djangoproject.com/en/1.6/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/1.6/ref/settings/
"""

from django.utils.translation import ugettext_lazy as _

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
import os
BASE_DIR = os.path.dirname(os.path.dirname(__file__))

{% if 'settings' in apps %}
SITE_ID = 1
{% endif %}

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/1.6/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = '{{ secret_key }}'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

TEMPLATE_DEBUG = True

ALLOWED_HOSTS = []


# Application definition

INSTALLED_APPS = (
    
    {% if not bare %}
    # Spices up the admin a bit
    'grappelli',
    # This comes in handy for rendering forms
    'widget_tweaks',
    # Ofcourse we need thumbnails
    'sorl.thumbnail',
    {% endif %}
    
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    {% if 'settings' in apps %}
    'django.contrib.sites',
    {% endif %}
    
    {% if not bare %}
    'django.contrib.humanize',
    {% endif %}
    
)

# Django loads templates from the first
# app that provides them. We want to allow
# your apps to override any default Sellmo templates.
# However Sellmo apps need to be carefully
# ordered to ensure correct chaining of functions.
# Therefor Sellmo detects and loads apps in a reversed
# order. To maintain clean ordering in this
# file we reverse Sellmo apps with this construct.

INSTALLED_APPS += tuple(reversed((
    
    'sellmo',
    
    {% if 'settings' in apps %}
    'sellmo.contrib.settings',
    'settings',
    {% endif %}
    
    {% if 'product' in apps %}
    {% if not bare %}
    'sellmo.contrib.product',
    'sellmo.contrib.product.subtypes.simple_product',
    {% endif %}
    'product',
    {% endif %}
    
    {% if 'pricing' in apps %}
    {% if not bare %}
    'sellmo.contrib.pricing',
    {% endif %}
    'pricing',
    {% endif %}
    
    {% if 'attribute' in apps %}
    'sellmo.contrib.attribute',
    'attribute',
    {% endif %}
    
    {% if 'brand' in apps %}
    'brand',
    {% endif %}
    
    {% if 'color' in apps %}
    'sellmo.contrib.color',
    'color',
    {% endif %}
    
    {% if 'variation' in apps %}
    'sellmo.contrib.variation',
    'variation',
    {% endif %}
    
    {% if 'category' in apps %}
    'sellmo.contrib.category',
    'category',
    {% endif %}
    
    {% if 'cart' in apps %}
    {% if not bare %}
    'sellmo.contrib.cart',
    {% endif %}
    'cart',
    {% endif %}
    
    {% if 'checkout' in apps %}
    {% if not bare %}
    'sellmo.contrib.checkout',
    'sellmo.contrib.checkout.multistep_checkout',
    {% endif %}
    'checkout',
    {% endif %}
    
    {% if 'payment' in apps %}
    'sellmo.contrib.payment',
    {% if not bare %}
    'sellmo.contrib.payment.methods.bank_transfer',
    'sellmo.contrib.payment.methods.cash_payment',
    {% endif %}
    'payment',
    {% endif %}
    
    {% if 'shipping' in apps %}
    'sellmo.contrib.shipping',
    {% if not bare %}
    'sellmo.contrib.shipping.methods.flat_shipping',
    'sellmo.contrib.shipping.methods.tiered_shipping',
    {% endif %}
    'shipping',
    {% endif %}
    
    {% if 'customer' in apps %}
    {% if not bare %}
    'sellmo.contrib.customer',
    'sellmo.contrib.customer.addresses.default_address',
    {% endif %}
    'customer',
    {% endif %}
    
    {% if 'account' in apps %}
    'sellmo.contrib.account',
    {% if not bare %}
    'sellmo.contrib.account.profile',
    'sellmo.contrib.account.registration',
    'sellmo.contrib.account.registration.simple_registration',
    {% endif %}
    {% if 'checkout' in apps %}
    'sellmo.contrib.account.checkout',
    {% endif %}
    'account',
    {% endif %}
    
    {% if 'discount' in apps %}
    # Put this before taxing to assure a correct pricing chain
    'sellmo.contrib.discount',
    {% if not bare %}
    'sellmo.contrib.discount.subtypes.percent_discount',
    {% endif %}
    'discount',
    {% endif %}
    
    {% if 'tax' in apps %}
    # Put this after other pricing apps
    # to assure a correct pricing chain
    'sellmo.contrib.tax',
    {% if not bare %}
    'sellmo.contrib.tax.subtypes.percent_tax',
    {% endif %}
    'tax',
    {% endif %}
    
    {% if 'availability' in apps %}
    'sellmo.contrib.availability',
    'availability',
    {% endif %}
    
    {% if 'search' in apps %}
    'sellmo.contrib.search',
    'search',
    {% endif %}
    
    {% if 'mailing' in apps %}
    'sellmo.contrib.mailing',
    'mailing',
    {% endif %}
    
    {% if 'store' in apps %}
    {% if not bare %}
    'sellmo.contrib.store',
    {% endif %}
    'store',
    {% endif %}
    
)))

INSTALLED_APPS += (
    
    # By including this, some admin templates
    # for polymorphism are overridden.
    'extras',
    
    {% if 'data' in apps %}
    # Overrides dumpdata and loaddata commands
    'sellmo.contrib.data',
    {% endif %}

    # Place admin after sellmo apps.
    # This way sellmo apps can load dependencies
    # first, after which ModelAdmin's can
    # be loaded by the Django Admin.
    'django.contrib.admin',
    
    {% if not bare %}
    # Comes in handy for debugging queries
    'debug_toolbar',
    {% endif %}
)

MIDDLEWARE_CLASSES = (
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'sellmo.core.middleware.LocalContextMiddleware',
)

TEMPLATE_CONTEXT_PROCESSORS = (
    'django.contrib.auth.context_processors.auth',
    'django.core.context_processors.debug',
    'django.core.context_processors.i18n',
    'django.core.context_processors.media',
    'django.core.context_processors.static',
    'django.core.context_processors.tz',
    'django.contrib.messages.context_processors.messages',
    # Needed by sellmo
    'django.core.context_processors.request',
    # Add Sellmo context processors
    {% if 'cart' in apps %}
    'sellmo.core.context_processors.cart_context',
    {% endif %}
    {% if 'customer' in apps %}
    'sellmo.core.context_processors.customer_context',
    {% endif %}
    {% if 'settings' in apps %}
    'sellmo.core.context_processors.settings_context',
    {% endif %}
    {% if 'account' in apps %}
    'sellmo.core.context_processors.login_form_context',
    {% endif %}
    {% if 'store' in apps and not bare %}
    'sellmo.core.context_processors.contact_form_context',
    {% endif %}
    {% if 'brand' in apps %}
    'sellmo.core.context_processors.brands_context',
    {% endif %}
)

ROOT_URLCONF = '{{ project_name }}.urls'

WSGI_APPLICATION = '{{ project_name }}.wsgi.application'


# Database
# https://docs.djangoproject.com/en/1.6/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': os.path.join(BASE_DIR, 'db.sqlite3'),
    }
}

# Internationalization
# https://docs.djangoproject.com/en/1.6/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_L10N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/1.6/howto/static-files/

STATIC_URL = 'http://localhost:8000/'

STATICFILES_DIRS = (
    os.path.join(BASE_DIR, '{{ project_name }}', 'static'),
)

# Media files (User uploaded files)

MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, '_media')


# Template files (HTML)

TEMPLATE_DIRS = (
    os.path.join(BASE_DIR, '{{ project_name }}', 'templates'),
)

{% if 'account' in apps %}
AUTH_USER_MODEL = 'account.User'
LOGIN_REDIRECT_URL = 'account.profile'
{% endif %}

{% if 'pricing' in apps %}
SELLMO_INDEXABLE_QTYS = [1, 9999999]
{% endif %}

{% if 'checkout' in apps and not bare %}
SELLMO_CHECKOUT_PROCESS = 'checkout.process.MultiStepCheckoutProcess'
SELLMO_ORDER_STATUSES = {
    'new' : (_("New"), {
        'initial' : True,
        'flow' : ['processing', 'completed', 'canceled'],
        'state' : 'new',
    }),
    'processing' : (_("Processing"), {
        'flow' : ['canceled', 'completed', 'on_hold'],
        'on_pending' : True,
        'state' : 'pending',
    }),
    'on_hold' : (_("On hold"), {
        'flow' : ['processing', 'completed'],
        'state' : 'pending',
    }),
    'completed' : (_("Completed"), {
        'flow' : ['closed', 'shipped'],
        'state' : 'completed',
        'on_completed' : True,
    }),
    'shipped' : (_("Shipped"), {
        'flow' : ['closed'],
        'state' : 'completed',
    }),
    'canceled' : (_("Canceled"), {
        'state' : 'canceled',
        'on_canceled' : True,
    }),
    'closed' : (_("Closed"), {
        'state' : 'closed',
        'on_closed' : True,
    }),
}
{% endif %}

{% if not bare %}
SELLMO_REPORT_GENERATORS = [
    'sellmo.contrib.reporting.generators.weasyprint_reporting.WeasyPrintReportGenerator'
]
SELLMO_REPORT_FORMAT = 'pdf'
SELLMO_REPORTING_PARAMS = {
    'pdf' : {
        'size' : 'A4',
        'margin' : '1cm',
        'zoom' : 1.0,
    },
    'png' : {
        'viewport' : '800x800'
    }
}
{% endif %}

{% if 'mailing' in apps and celery %}
SELLMO_MAIL_HANDLER = 'sellmo.contrib.mailing.handlers.celery_mailing.CeleryMailHandler'
{% endif %}

{% if 'search' in apps %}
SELLMO_SEARCH_FIELDS = ['name', 'sku']
{% endif %}

{% if celery %}
SELLMO_CELERY_ENABLED = True
{% endif %}

{% if caching %}
SELLMO_CACHING_ENABLED = True
{% endif %}

{% if not bare %}
GRAPPELLI_ADMIN_TITLE = '{{ project_name|capfirst }}'
{% endif %}

{% if not bare %}
SHOW_DEBUG_TOOLBAR = False
def show_toolbar_callback(request):
    return DEBUG and SHOW_DEBUG_TOOLBAR
    
DEBUG_TOOLBAR_CONFIG = {
    'SHOW_TOOLBAR_CALLBACK': '{{ project_name }}.settings.show_toolbar_callback'
}
{% endif %}