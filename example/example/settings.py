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


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/1.6/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = 'dh@py67-9&)ul2)su7$b66a*3qox=p82fphz0*zlh3&%ly^lxh'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

TEMPLATE_DEBUG = True

ALLOWED_HOSTS = []


# Application definition

INSTALLED_APPS = (
    
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    
    'django.contrib.sites',
    
    
    'sellmo',
    
    
    'sellmo.contrib.settings',
    'settings',
    
    
    
    
    'sellmo.contrib.product',
    'sellmo.contrib.product.subtypes.simple_product',
    
    'product',
    
    
    
    'sellmo.contrib.attribute',
    'attribute',
    
    
    
    'sellmo.contrib.variation',
    'variation',
    
    
    
    'sellmo.contrib.category',
    'category',
    
    
    
    
    'sellmo.contrib.cart',
    
    'cart',
    
    
    
    
    'sellmo.contrib.checkout',
    
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
    
    
    
    
    
    
    
    
    
    
    
    'sellmo.contrib.mailing',
    'mailing',
    
    
    
    
    'sellmo.contrib.store',
    
    'store',
    
    
    # By including this, some admin templates
    # for polymorphism are overridden.
    'sellmo.contrib.polymorphism',
    
    
    
    # Place admin after sellmo apps.
    # This way sellmo apps can load dependencies
    # first, after which ModelAdmin's can
    # be loaded by the Django Admin.
    'django.contrib.admin',

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

STATIC_URL = '/static/'

STATICFILES_DIRS = (
    os.path.join(BASE_DIR, 'assets'),
)

# Template files (HTML)

TEMPLATE_DIRS = (
    os.path.join(BASE_DIR, 'templates'),
)


AUTH_USER_MODEL = 'account.User'
LOGIN_REDIRECT_URL = 'account.profile'





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









