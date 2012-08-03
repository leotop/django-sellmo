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
	
	Addressee = models.Model
	Address = models.Model
	Customer = models.Model
	
	_CustomerForm = None
	_AddressForm = None
	
	def __init__(self, *args, **kwargs):
		from sellmo.api.customer.models import Addressee, Customer, Address
		self.Addressee = Addressee
		self.Address = Address
		self.Customer = Customer
		
		# Init forms
		from sellmo.api.customer.forms import CustomerForm, AddressForm
		self._CustomerForm = CustomerForm
		self._AddressForm = AddressForm
	
	@get()
	def get_customer_form(self, chain, data=None, customer=None, form=None, **kwargs):
		if form == None:
			form = self._CustomerForm(data, prefix='customer', instance=customer)
		if chain:
			return chain.execute(data=data, customer=customer, form=form, **kwargs)
		return form
		
	@get()
	def get_address_form(self, chain, prefix, data=None, address=None, form=None, **kwargs):
		if form == None:
			form = self._AddressForm(data, prefix='address' if not prefix else 'address_%s' % prefix, instance=address)
		if chain:
			return chain.execute(prefix=prefix, data=data, address=address, form=form, **kwargs)
		return form
		
	@view()
	def address_form(self, chain, request, prefix, user=None, context=None, **kwargs):
		if context == None:
			context = {}
	
		customer = self.Customer.objects.from_request(request)
		try:
			address = customer.addresses.get(type=prefix)
		except self.Address.DoesNotExist:
			address = None
		
		if request.method == 'POST':
			form = self.get_address_form(prefix=prefix, data=request.POST, address=address)
			if form.is_valid():
				address = form.save(commit=False)
				address.type = prefix
				address.customer = customer
				address.save()
		else:
			form = self.get_address_form(prefix=prefix, address=address)
			
		# Append to context
		context['%s_address_form' % prefix] = form
		
		if chain:
			chain.execute(request, context=context, **kwargs)
			
	@view()
	def customer_form(self, chain, request, context=None, **kwargs):
		if context == None:
			context = {}
			
		customer = self.Customer.objects.from_request(request)
		if request.method == 'POST':
			form = self.get_customer_form(data=request.POST, customer=customer)
			if form.is_valid():
				customer = form.save()
				customer.track(request)
		else:
			form = self.get_customer_form(customer=customer)
			
		# Append to context
		context['customer_form'] = form
		
		if chain:
			chain.execute(request, form=form, context=context, **kwargs)