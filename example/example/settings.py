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


SITE_ID = 1


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/1.6/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = '%mc*j!odth64qhdbeh!t64p3wj^@g!i=$f5u_3#8prf=j(s3ht'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

TEMPLATE_DEBUG = True

ALLOWED_HOSTS = []


# Application definition

INSTALLED_APPS = (
    
    
    # Spices up the admin a bit
    'grappelli',
    # This comes in handy for rendering forms
    'widget_tweaks',
    # Ofcourse we need thumbnails
    'sorl.thumbnail',
    
    
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    
    'django.contrib.sites',
    
    
    
    'django.contrib.humanize',
    
    
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
    
    
    'sellmo.contrib.settings',
    'settings',
    
    
    
    
    'sellmo.contrib.product',
    'sellmo.contrib.product.subtypes.simple_product',
    
    'product',
    
    
    
    
    'sellmo.contrib.pricing',
    
    'pricing',
    
    
    
    'sellmo.contrib.attribute',
    'attribute',
    
    
    
    'brand',
    
    
    
    'sellmo.contrib.color',
    'color',
    
    
    
    'sellmo.contrib.variation',
    'variation',
    
    
    
    'sellmo.contrib.category',
    'category',
    
    
    
    
    'sellmo.contrib.cart',
    
    'cart',
    
    
    
    
    'sellmo.contrib.checkout',
    'sellmo.contrib.checkout.multistep_checkout',
    
    'checkout',
    
    
    
    'sellmo.contrib.payment',
    
    'sellmo.contrib.payment.methods.bank_transfer',
    'sellmo.contrib.payment.methods.cash_payment',
    
    'payment',
    
    
    
    'sellmo.contrib.shipping',
    
    'sellmo.contrib.shipping.methods.flat_shipping',
    'sellmo.contrib.shipping.methods.tiered_shipping',
    
    'shipping',
    
    
    
    
    'sellmo.contrib.customer',
    'sellmo.contrib.customer.addresses.default_address',
    
    'customer',
    
    
    
    'sellmo.contrib.account',
    
    'sellmo.contrib.account.profile',
    'sellmo.contrib.account.registration',
    'sellmo.contrib.account.registration.simple_registration',
    
    
    'sellmo.contrib.account.checkout',
    
    'account',
    
    
    
    # Put this before taxing to assure a correct pricing chain
    'sellmo.contrib.discount',
    
    'sellmo.contrib.discount.subtypes.percent_discount',
    
    'discount',
    
    
    
    # Put this after other pricing apps
    # to assure a correct pricing chain
    'sellmo.contrib.tax',
    
    'sellmo.contrib.tax.subtypes.percent_tax',
    
    'tax',
    
    
    
    'sellmo.contrib.availability',
    'availability',
    
    
    
    
    
    'sellmo.contrib.mailing',
    'mailing',
    
    
    
    
    'sellmo.contrib.store',
    
    'store',
    
    
)))

INSTALLED_APPS += (
    
    # By including this, some admin templates
    # for polymorphism are overridden.
    'extras',
    
    

    # Place admin after sellmo apps.
    # This way sellmo apps can load dependencies
    # first, after which ModelAdmin's can
    # be loaded by the Django Admin.
    'django.contrib.admin',
    
    
    # Comes in handy for debugging queries
    'debug_toolbar',
    
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
    
    'sellmo.core.context_processors.cart_context',
    
    
    'sellmo.core.context_processors.customer_context',
    
    
    'sellmo.core.context_processors.settings_context',
    
    
    'sellmo.core.context_processors.login_form_context',
    
    
    'sellmo.core.context_processors.contact_form_context',
    
    
    'sellmo.core.context_processors.brands_context',
    
)

ROOT_URLCONF = 'example.urls'

WSGI_APPLICATION = 'example.wsgi.application'


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
    os.path.join(BASE_DIR, 'example', 'static'),
)

# Media files (User uploaded files)

MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, '_media')


# Template files (HTML)

TEMPLATE_DIRS = (
    os.path.join(BASE_DIR, 'example', 'templates'),
)


AUTH_USER_MODEL = 'account.User'
LOGIN_REDIRECT_URL = 'account.profile'



SELLMO_INDEXABLE_QTYS = [1, 9999999]



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











GRAPPELLI_ADMIN_TITLE = 'Example'



SHOW_DEBUG_TOOLBAR = False
def show_toolbar_callback(request):
    return DEBUG and SHOW_DEBUG_TOOLBAR
    
DEBUG_TOOLBAR_CONFIG = {
    'SHOW_TOOLBAR_CALLBACK': 'example.settings.show_toolbar_callback'
}
