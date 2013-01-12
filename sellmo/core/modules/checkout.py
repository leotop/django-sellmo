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

from django.db import models
from django import dispatch

#

import sellmo
from sellmo import modules
from sellmo.api.decorators import view, get

#

class CheckoutModule(sellmo.Module):

	namespace = 'checkout'
	prefix = 'checkout'
	enabled = True
	
	Order = models.Model
	OrderLine = models.Model
	
	collect_shipping_methods = dispatch.Signal(providing_args=['methods'])
	collect_payment_methods = dispatch.Signal(providing_args=['methods'])
	
	def __init__(self, *args, **kwargs):
		from sellmo.api.checkout.models import Order, OrderLine
		self.Order = Order
		self.OrderLine = OrderLine
		
	@view(r'$')
	def checkout(self, chain, request, cart=None, context=None, **kwargs):
		if context == None:
			context = {}
		
		#
		modules.customer.customer_form(request, context=context)
		modules.customer.address_form(request, prefix='billing', context=context)
		
		#
		#self.on_shipping_method_form(request, context=context, **kwargs)
		#self.on_payment_method_form(request, context=context, **kwargs)
		
		#
		if chain:
			return chain.execute(request, cart=cart, context=context, **kwargs)
		
	@get()
	def get_shipping_method_form(self, chain, data=None, methods=None, **kwargs):
		
		#
		if methods == None:
			methods = []
			self.collect_shipping_methods.send(sender=self, methods=methods)
		
		#
		if data == None:
			form = self._ShippingMethodForm(methods=methods, **kwargs)
		else:
			form = _ShippingMethodForm(data, methods=methods)
		
		if chain:
			return chain.execute(form=form, post=post, methods=methods, context=context, **kwargs)
		
		return form
			
	@view()
	def shipping_method_form(self, chain, request, methods=None, context=None, **kwargs):
		if context == None:
			context = {}
		
		#
		context['shipping_method'] = self.get_shipping_method_form(post=request.POST)
			
		#
		if chain:
			chain.execute(request, context=context, **kwargs)