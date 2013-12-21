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

class BankTransferInstructionsStep(CheckoutStep):

	invalid_context = None
	key = 'bank_transfer_instructions'

	def __init__(self, order, request, next_step):
		super(BankTransferInstructionsStep, self).__init__(order=order, request=request)
		self.next_step = next_step
		self.payment = self.order.payment.downcast()

	def is_completed(self):
		return False

	def can_skip(self):
		return False

	def get_next_step(self):
		return self.next_step

	def _contextualize_or_complete(self, request, context, data=None):
		success = True
		return success

	def complete(self, data):
		self.invalid_context = {}
		return self._contextualize_or_complete(self.request, self.invalid_context, data)

	def render(self, request, context):
		if not self.invalid_context:
			self._contextualize_or_complete(request, context)
		else:
			context.update(self.invalid_context)

		return modules.bank_transfer.instructions(request=request, order=self.order, context=context)





