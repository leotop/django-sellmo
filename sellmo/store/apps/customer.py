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
from django.http import Http404
from django.shortcuts import redirect

#

import sellmo
from sellmo import apps
from sellmo.store.decorators import view, get

#

class CustomerApp(sellmo.App):

	namespace = 'customer'
	prefix = 'customer'
	enabled = True
	
	Person = models.Model
	Address = models.Model
	Customer = models.Model
	
	_CustomerForm = None
	_AddressForm = None
	
	def __init__(self, *args, **kwargs):
		from sellmo.api.customer.models import Person, Customer, Address
		self.Person = Person
		self.Address = Address
		self.Customer = Customer
		
		# Init forms
		from sellmo.api.customer.forms import CustomerForm, AddressForm
		self._CustomerForm = CustomerForm
		self._AddressForm = AddressForm
	
	@get()
	def customer_form(self, chain, user=None, context=None, **kwargs):
		if context == None:
			context = {
				'form': self._CustomerForm({})
			}
		if chain:
			return chain.execute(user=user, context=context, **kwargs)
		return context
		
	@get()
	def address_form(self, chain, type=None, user=None, context=None, **kwargs):
		if context == None:
			context = {
				'form': self._AddressForm(prefix=type)
			}
		if chain:
			return chain.execute(user=user, context=context, **kwargs)
		return context
		
	@view()
	def on_address_form(self, chain, request, type=None, user=None, context=None, **kwargs):
		if context == None:
			context = {}
	
		if request.method == 'POST':
			form = self._AddressForm(request.POST, prefix=prefix)
		else:
			form = self.address_form(type=type, user=user, **kwargs)['form']
			
		# Append to context
		if type:
			context['%s_address_form' % type] = form
		else:
			context['address_form'] = form
		
		if chain:
			chain.execute(request, form=form, context=context, **kwargs)
			
	@view()
	def on_customer_form(self, chain, request, context=None, **kwargs):
		if context == None:
			context = {}
	
		if request.method == 'POST':
			form = self._CustomerForm(request.POST)
		else:
			form = self.customer_form(**kwargs)['form']
			
		# Append to context
		context['customer_form'] = form
		
		if chain:
			chain.execute(request, form=form, context=context, **kwargs)