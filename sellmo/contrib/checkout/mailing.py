# Copyright (c) 2014, Adaptiv Design
# All rights reserved.
# 
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:

# 1. Redistributions of source code must retain the above copyright notice,
# this list of conditions and the following disclaimer.

# 2. Redistributions in binary form must reproduce the above copyright notice,
# this list of conditions and the following disclaimer in the documentation
# and/or other materials provided with the distribution.

# 3. Neither the name of the copyright holder nor the names of its contributors
# may be used to endorse or promote products derived from this software without
# specific prior written permission.

# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
# ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE
# LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR
# CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF
# SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS
# INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN
# CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)
# ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
# POSSIBILITY OF SUCH DAMAGE.


from sellmo import modules
from sellmo.api.mailing import MailWriter
from sellmo.core.reporting import reporter
from sellmo.core.mailing import mailer

from django.utils.translation import ugettext_lazy as _


ORDER_MAILS = {
    'order_confirmation': {
        'writer': ('sellmo.contrib.checkout.mailing'
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
        'writer': ('sellmo.contrib.checkout.mailing'
                   '.OrderNotificationWriter'),
        'send_once': True,
        'send_events': [
            {
                'on_pending': True,
            }
        ]
    },
    'shipping_notification': {
        'writer': ('sellmo.contrib.checkout.mailing'
                   '.ShippingNotificationWriter'),
        'send_once': True,
        'send_events': [
            {
                'status': 'shipped',
            }
        ]
    }
}


def send_order_mails(order, event_signature=None):
    # Update event_signature
    if event_signature is None:
        event_signature = {}
    if order.payment:
        event_signature['instant_payment'] = order.payment.instant

    for mail, config in modules.checkout.order_mails.iteritems():
        for event in config['send_events']:
            for key, value in event.iteritems():
                # Make sure signature is a match
                if (not key in event_signature or
                        not event_signature[key] == value):
                    break
            else:
                # Did have a match
                break
        else:
            # Did not found a match
            continue
        # Did have a match

        send_once = config.get('send_once', False)
        if send_once:
            send_mails = modules.checkout.OrderMail.objects.filter(
                order=order,
                status__message_type=mail,
                status__delivered=True
            )
            if send_mails.count() > 0:
                # Do not send
                continue

        mailer.send_mail(mail, {
            'order': order
        })


class OrderConfirmationWriter(MailWriter):

    formats = ['html', 'text']

    def __init__(self, order):
        self.order = order

    def get_subject(self):
        return _("Order confirmation")

    def get_body(self, format):
        return modules.checkout.render_order_confirmation_email(
            format=format, order=self.order)

    def get_to(self):
        return self.order.email

    def get_attachments(self):
        if reporter.can_report('order_confirmation'):
            report = reporter.get_report('order_confirmation', context={
                'order': self.order
            })
            return [
                (report.filename, report.data, report.mimetype)
            ]


class OrderNotificationWriter(MailWriter):

    formats = ['html', 'text']

    def __init__(self, order):
        self.order = order

    def get_subject(self):
        return _("Order notification")

    def get_body(self, format):
        return modules.checkout.render_order_notification_email(
            format=format, order=self.order)

    def get_to(self):
        return modules.checkout.notification_to_email

    def get_attachments(self):
        if reporter.can_report('order_confirmation'):
            report = reporter.get_report('order_confirmation', context={
                'order': self.order,
                'internal': True,
            })
            return [
                (report.filename, report.data, report.mimetype)
            ]


class ShippingNotificationWriter(MailWriter):

    formats = ['html', 'text']

    def __init__(self, order):
        self.order = order

    def get_subject(self):
        return _("Shipping notification")

    def get_body(self, format):
        return modules.checkout.render_shipping_notification_email(
            format=format, order=self.order)

    def get_to(self):
        return self.order.email
        
    def get_attachments(self):
        if reporter.can_report('invoice'):
            report = reporter.get_report('invoice', context={
                'order': self.order,
            })
            return [
                (report.filename, report.data, report.mimetype)
            ]
