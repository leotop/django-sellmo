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


ACCEPT_TERMS_ENABLED = True
INVOICE_WRITER = 'sellmo.contrib.contrib_checkout.reporting.InvoiceWriter'
NOTIFICATION_MAIL_TO = django_settings.DEFAULT_FROM_EMAIL


CHECKOUT_MAILS = {
    'order_confirmation': {
        'writer': ('sellmo.contrib.contrib_checkout.mailing'
                   '.OrderConfirmationWriter'),
        'send_once': True,
        'send_events': [
            {
                'on_paid': True,
                'instant_payment': True
            },
            {
                'on_pending': True,
                'instant_payment': False
            }
        ]
    },
    'order_notification': {
        'writer': ('sellmo.contrib.contrib_checkout.mailing'
                   '.OrderNotificationWriter'),
        'send_once': True,
        'send_events': [
            {
                'on_pending': True,
            }
        ]
    },
    'shipping_notification': {
        'writer': ('sellmo.contrib.contrib_checkout.mailing'
                   '.ShippingNotificationWriter'),
        'send_once': True,
        'send_events': [
            {
                'status': 'shipped',
            }
        ]
    }
}
