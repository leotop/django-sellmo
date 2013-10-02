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
from sellmo.api.checkout.processes import CheckoutProcess, CheckoutStep

#

class MultiStepCheckoutProcess(CheckoutProcess):
	
	def get_first_step(self):
		return LoginStep(order=self.order, request=self.request)
	
class LoginStep(CheckoutStep):
	
	invalid_context = None
	key = 'login'
	
	def is_completed(self):
		return self.request.user.is_authenticated()
		
	def can_skip(self):
		return not modules.checkout_process.login_required
		
	def get_next_step(self):
		return CustomerStep(order=self.order, request=self.request)
		
	def _contextualize_or_complete(self, request, context, data=None):
		success = True
		
		user, form, processed = modules.customer.handle_login(request=request, prefix='login', data=data)
		context['login_form'] = form
		success &= processed
		
		return success
		
	def complete(self, data):
		self.invalid_context = {}
		return self._contextualize_or_complete(self.request, self.invalid_context, data)
		
	def render(self, request, context):
		if not self.invalid_context:
			self._contextualize_or_complete(request, context)
		else:
			context.update(self.invalid_context)
		
		return modules.checkout_process.login(request=request, context=context)
		
class CustomerStep(CheckoutStep):
	
	invalid_context = None
	key = 'customer'
	
	def is_completed(self):
		for type in modules.checkout.required_address_types:
			if self.order.get_address(type) is None:
				return False
		return True
		
	def _contextualize_or_complete(self, request, context, data=None):
		success = True
		addresses = {}
		
		contactable, form, processed = modules.customer.handle_contactable(request=request, prefix='contactable', contactable=self.order, data=data)
		context['contactable_form'] = form
		success &= processed
		
		for type in modules.checkout.required_address_types:
			address, form, processed = modules.customer.handle_address(request=request, type=type, prefix='{0}_address'.format(type), address=self.order.get_address(type), data=data)
			context['{0}_address_form'.format(type)] = form
			success &= processed
			addresses[type] = address
		
		if success:
			for type in modules.checkout.required_address_types:
				address = addresses[type]
				address.save()
				self.order.set_address(type, address)
			self.order.save()
		
		return success
		
	def complete(self, data):
		self.invalid_context = {}
		return self._contextualize_or_complete(self.request, self.invalid_context, data)
		
	def render(self, request, context):
		if not self.invalid_context:
			self._contextualize_or_complete(request, context)
		else:
			context.update(self.invalid_context)
		
		return modules.checkout_process.customer(request=request, context=context)
		
	