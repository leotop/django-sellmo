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

from sellmo import modules
from sellmo.signals.checkout import order_paid, order_state_changed, order_status_changed
from sellmo.signals.mailing import mail_init
from sellmo.core.mailing import mailer
from sellmo.core.reporting import reporter
from sellmo.contrib.contrib_checkout.mailing import send_order_mails
from sellmo.contrib.contrib_checkout.reporting import InvoiceWriter
from sellmo.contrib.contrib_checkout.config import settings

# Validate & Register mail writers
for message_type, config in settings.CHECKOUT_MAILS.iteritems():
	if 'writer' not in config:
		raise Exception("{0} has no writer configured.".format(message_type))
	if 'send_events' not in config or not config['send_events']:
		raise Exception("{0} has no send_events configured.".format(message_type))
	mailer.register(message_type, config['writer'])

# Register report writers
reporter.register('invoice', settings.INVOICE_WRITER)
	
#

def on_mail_init(sender, message_type, message_reference, context, **kwargs):
	if message_type in settings.CHECKOUT_MAILS:
		try:
			status = modules.mailing.MailStatus.objects.get(message_reference=message_reference)
		except modules.mailing.MailStatus.DoesNotExist:
			logger.warning("Mail message {0} could not be linked to order {1}.".format(message_reference, context['order']))
		else:
			modules.checkout_mailing.OrderMail.objects.create(
				status=status,
				order=context['order'],
			)

mail_init.connect(on_mail_init)

#

def on_order_paid(sender, order, **kwargs):
	send_order_mails(order, {
		'on_paid' : True,
	})
	
def on_order_state_changed(sender, order, new_state, old_state=None, **kwargs):
	send_order_mails(order, {
		'state' : new_state,
		'on_{0}'.format(new_state) : True,
	})
	
def on_order_status_changed(sender, order, new_status, old_status=None, **kwargs):
	send_order_mails(order, {
		'status' : new_status,
	})
	

order_paid.connect(on_order_paid)
order_state_changed.connect(on_order_state_changed)
order_status_changed.connect(on_order_status_changed)
