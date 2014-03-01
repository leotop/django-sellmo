# Copyright (c) 2012, Adaptiv Design
# All rights reserved.
# 
# Redistribution and use in source and binary forms, with or without modification,
# are permitted provided that the following conditions are met:
#
#     * Redistributions of source code must retain the above copyright notice, this
# list of conditions and the following disclaimer.
#     * Redistributions in binary form must reproduce the above copyright notice,
# this list of conditions and the following disclaimer in the documentation and/or
# other materials provided with the distribution.
#    * Neither the name of the <ORGANIZATION> nor the names of its contributors may
# be used to endorse or promote products derived from this software without specific
# prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND
# ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE DISCLAIMED.
# IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT,
# INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT
# NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR
# PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY,
# WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)
# ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
# POSSIBILITY OF SUCH DAMAGE.

from django.conf import settings as django_settings
from django.utils.translation import ugettext_lazy as _


#

CURRENCY = ('eur', _(u"euro"), _(u"\u20ac {amount:\u00a0>{align}.2f}"))

ADD_TO_CART_FORM = 'sellmo.api.cart.forms.AddToCartForm'
EDIT_PURCHASE_FORM = 'sellmo.api.cart.forms.EditPurchaseForm'

def method_choice_format(method, costs, **kwargs):
    if costs:
        return u"{method} +{costs}".format(method=method, costs=costs)
    return u"{method}".format(method=method)

PAYMENT_METHOD_CHOICE_FORMAT = method_choice_format
SHIPPING_METHOD_CHOICE_FORMAT = method_choice_format

CUSTOMER_REQUIRED = False
EMAIL_REQUIRED = True
BUSINESSES_ONLY = False
BUSINESSES_ALLOWED = True
ADDRESS_TYPES = ['shipping', 'billing']
AUTH_ENABLED = True

ORDER_STATUSES = {
    'new' : (_("New"), {
        'initial' : True,
        'flow' : ['awaiting_payment', 'processing', 'completed', 'canceled'],
        'state' : 'new',
    }),
    'awaiting_payment' : (_("Awaiting payment"), {
        'flow' : ['canceled', 'payment_received'],
        'on_pending' : True,
        'state' : 'pending',
    }),
    'payment_received' : (_("Payment received"), {
        'flow' : ['processing'],
        'on_paid' : True,
        'state' : 'pending',
    }),
    'processing' : (_("Processing"), {
        'flow' : ['canceled', 'completed', 'on_hold'],
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


#

REDIRECTION_SESSION_PREFIX = '_sellmo_redirection'
REDIRECTION_DEBUG = False

#

CACHING_PREFIX = '_sellmo'
CACHING_ENABLED = True

#

CELERY_ENABLED = False

#

MAIL_HANDLER = 'sellmo.core.mailing.handlers.DefaultMailHandler'
MAIL_FROM = django_settings.DEFAULT_FROM_EMAIL

# 

REPORT_GENERATORS = []
REPORT_FORMAT = 'pdf'