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
from sellmo.api.pricing import Price
from sellmo.api.checkout import PaymentMethod

#

from sellmo.contrib.contrib_payment.methods.ideal.mollie_ideal.process import *

#

from django.utils.translation import ugettext_lazy as _

#
	
class MollieIdealPaymentMethod(PaymentMethod):

	identifier = 'ideal'
	name = _("iDeal")
		
	def process(self, order, request, next_step):
		if order.is_paid:
			return next_step
		
		# Get our payment 
		payment = order.payment.downcast()
		
		# Check status
		if payment.is_pending:
			# Did not (yet) receive a response from mollie
			return MollieIdealPendingStep(order=order, request=request, next_step=next_step)
		elif payment.is_completed and not payment.is_success:
			# Transaction has failed
			return MollieIdealFailureStep(order=order, request=request, next_step=next_step)
		
		return MollieIdealBankSelectStep(order=order, request=request, next_step=next_step)
		
	def new_payment(self, order):
		return modules.mollie_ideal.MollieIdealPayment()

	def get_costs(self, order, currency=None, **kwargs):
		return modules.pricing.get_price(price=Price(0), payment_method=self)
		
	def __unicode__(self):
		settings = modules.payment.get_settings()
		if settings.mollie_ideal_description:
			return settings.mollie_ideal_description
		return super(MollieIdealPaymentMethod, self).__unicode__()
		