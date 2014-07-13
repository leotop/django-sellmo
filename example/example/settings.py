"""
Django settings for skeleton project.

For more information on this file, see
https://docs.djangoproject.com/en/1.6/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/1.6/ref/settings/
"""

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
import os
BASE_DIR = os.path.dirname(os.path.dirname(__file__))


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/1.6/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = 'kl2a)2o3!re@arvbn7m*icca^=+10_zb)z9d)%c@j@!s0cod0b'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

TEMPLATE_DEBUG = True

ALLOWED_HOSTS = []


# Application definition

INSTALLED_APPS = (
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.sites',
    
    # This comes in handy for rendering forms
    'widget_tweaks',
    
    # Use South for model migrations
    'south',
    
    # --- Sellmo BEGIN ---
    
    # !! Include this localization purposes
    'sellmo',
    
    # !! Needs to be first, loads Sellmo core modules.
    'sellmo.boot.boot_modules',
    
    # !! Enables user settings, required for certain contrib apps.
    'sellmo.contrib.settings',
    'settings',
    
    # Enhances Sellmo's core mailing functionality.
    'sellmo.contrib.mailing',
    'mailing',
    
    # Enhances Sellmo's basic Product definition.
    'sellmo.contrib.product',
    # At least 1 Product subtype is needed.
    'sellmo.contrib.product.subtypes.simple_product',
    'product',
    
    'sellmo.contrib.category',
    'category',
    
    'sellmo.contrib.attribute',
    'attribute',
    
    'sellmo.contrib.search',
    
    'sellmo.contrib.pricing',
    'pricing',
    
    'sellmo.contrib.variation',
    'variation',
    
    'sellmo.contrib.cart',
    'cart',
    
    'sellmo.contrib.tax',
    'sellmo.contrib.tax.subtypes.percent_tax',
    'tax',
    
    'sellmo.contrib.customer',
    'sellmo.contrib.customer.addresses.default_address',
    'customer',
    
    'sellmo.contrib.account',
    'sellmo.contrib.account.profile',
    'sellmo.contrib.account.registration',
    'sellmo.contrib.account.registration.simple_registration',
    'account',
    
    'sellmo.contrib.shipping',
    'sellmo.contrib.shipping.methods.flat_shipping',
    'sellmo.contrib.shipping.methods.tiered_shipping',
    'shipping',
    
    'sellmo.contrib.payment',
    'sellmo.contrib.payment.methods.bank_transfer',
    'sellmo.contrib.payment.methods.cash_payment',
    'payment',
    
    'sellmo.contrib.checkout',
    'sellmo.contrib.checkout.multistep_checkout',
    'checkout',
    
    'sellmo.contrib.store',
    'store',
    
    # Enables polymorphism in admin
    'sellmo.contrib.polymorphism',
    
    # Makes Sellmo fixtures work.
    'sellmo.contrib.data',
    
    # !! Needs to be last, this starts up Sellmo.
    'sellmo.boot.boot_sellmo',
    
    # --- Sellmo END ---
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
)

MIDDLEWARE_CLASSES = (
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    # Add Sellmo middleware
    'sellmo.core.middleware.LocalContextMiddleware',
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

# Settings for django.contrib.auth 

AUTH_USER_MODEL = 'account.User'
LOGIN_REDIRECT_URL = 'account.profile'


# Settings for django.contrib.sites

SITE_ID = 1


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/1.6/howto/static-files/

STATIC_URL = '/static/'

STATICFILES_DIRS = (
    os.path.join(BASE_DIR, 'example/assets'),
)


# Template files (HTML)

TEMPLATE_DIRS = (
    os.path.join(BASE_DIR, 'example/templates'),
)


# Logging

LOGGING = {
    'disable_existing_loggers': False,
    'version': 1,
    'handlers': {
        'console': {
            # logging handler that outputs log messages to terminal
            'class': 'logging.StreamHandler',
            'level': 'DEBUG', # message level to be written to console
        },
    },
    'loggers': {
        '': {
            'handlers': ['console'],
            'level': 'INFO',
            'propagate': False,
        },
    },
}