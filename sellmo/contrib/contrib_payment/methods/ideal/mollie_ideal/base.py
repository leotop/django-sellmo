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

from sellmo.api.checkout.processes import CheckoutProcess, CheckoutStep

#

class MollieIdealBankSelectStep(CheckoutStep):
	
	invalid_context = None
	key = 'ideal_bank_select'
	
	def __init__(self, order, request, next_step):
		super(MollieIdealBankSelectStep, self).__init__(order=order, request=request)
		self.next_step = next_step
		self.payment = self.order.payment.downcast()
	
	def is_completed(self):
		return not self.payment.bank_id is None
		
	def can_skip(self):
		return False
		
	def get_next_step(self):
		return MollieIdealRedirectStep(order=self.order, request=self.request, next_step=self.next_step)
		
	def _contextualize_or_complete(self, request, context, data=None):
		success = True
		
		bank, form, processed = modules.mollie_ideal.handle_bank_select(request=request, payment=self.payment, prefix='bank_select', data=data)
		context['bank_select_form'] = form
		success &= processed
		
		if success:
			self.payment.save()
		
		return success
		
	def complete(self, data):
		self.invalid_context = {}
		return self._contextualize_or_complete(self.request, self.invalid_context, data)
		
	def render(self, request, context):
		if not self.invalid_context:
			self._contextualize_or_complete(request, context)
		else:
			context.update(self.invalid_context)
		
		return modules.mollie_ideal.bank_select(request=request, context=context)
	
#

class MollieIdealRedirectStep(CheckoutStep):

	invalid_context = None
	key = 'ideal_redirect'

	def __init__(self, order, request, next_step):
		super(MollieIdealRedirectStep, self).__init__(order=order, request=request)
		self.next_step = next_step

	def is_completed(self):
		return False

	def can_skip(self):
		return False

	def get_next_step(self):
		return None

	def render(self, request, context):
		return modules.mollie_ideal.redirect(request=request, order=self.order, contex=context)
	
class MollieIdealPaymentMethod(PaymentMethod):

	def __init__(self, identifier, description):
		super(MollieIdealPaymentMethod, self).__init__(identifier, description)
		
	def process(self, order, request, next_step):
		if order.is_paid:
			return next_step
		
		# Get our payment 
		payment = order.payment.downcast()
		
		# Check status
		if payment.is_pending:
			# Did not yet receive a response from mollie
			return MolliePendingStep(order=order, request=request, next_step=next_step)
		
		# Either this is the first time a payment is attempted, or a payment was
		# not successful thus allow the user to pay (again)
		return MollieIdealBankSelectStep(order=order, request=request, next_step=next_step)
		
	def new_payment(self, order):
		return modules.mollie_ideal.MollieIdealPayment(identifier=self.identifier)

	def get_costs(self, order, currency=None, **kwargs):
		return modules.pricing.get_price(price=Price(0), payment_method=self)

	def __unicode__(self):
		description = self.description
		return description
		