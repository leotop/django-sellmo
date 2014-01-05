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

from django import forms
from django.http import HttpResponse, Http404
from django.core.urlresolvers import reverse
from django.shortcuts import redirect, render_to_response
from django.contrib.sites.models import Site

#

from sellmo import modules, Module
from sellmo.api.decorators import view, chainable
from sellmo.contrib.contrib_payment.methods.ideal.mollie_ideal.models import MollieIdealPayment

#

import requests
from lxml import etree
from lxml import objectify

#

class MollieIdealModule(Module):
	namespace = 'mollie_ideal'
	
	#
	BankSelectForm = forms.Form
	MollieIdealPayment = MollieIdealPayment
	
	#
	mollie_banklist_url = 'https://secure.mollie.nl/xml/ideal?a=banklist'
	mollie_fetch_url = 'https://www.mollie.nl//xml/ideal?a=fetch'
	mollie_check_url = 'https://secure.mollie.nl/xml/ideal?a=check'
	
	@view()
	def bank_select(self, chain, request, context=None, **kwargs):
		if context is None:
			context = {}
		if chain:
			return chain.execute(request=request, context=context, **kwargs)
		else:
			# We don't render anything
			raise Http404
			
	@view()
	def pending(self, chain, request, context=None, **kwargs):
		if context is None:
			context = {}
		if chain:
			return chain.execute(request=request, context=context, **kwargs)
		else:
			# We don't render anything
			raise Http404
			
	@view()
	def failure(self, chain, request, context=None, **kwargs):
		if context is None:
			context = {}
		if chain:
			return chain.execute(request=request, context=context, **kwargs)
		else:
			# We don't render anything
			raise Http404
		
	@view(r'^report$')
	def report(self, chain, request, **kwargs):
		transaction_id = request.GET.get('transaction_id', None)
		
		# Find a payment
		try:
			payment = self.MollieIdealPayment.objects.get(transaction_id=transaction_id)
		except self.MollieIdealPayment.DoesNotExist:
			raise Http404
			
		# We received a report, save now
		payment.transaction_report = True
		payment.save()
			
		# Get the order
		order = payment.order
		
		# Now get status
		settings = modules.payment.get_settings()
		
		payload = {
			'partnerid' : settings.mollie_partner_id,
			'transaction_id' : payment.transaction_id,
		}
		
		if settings.test_mode:
			payload['testmode'] = 'true'
		
		req = requests.get(self.mollie_check_url, params=payload)
		if req.status_code != requests.codes.ok:
			raise Exception()
		
		root = objectify.fromstring(req.text)
		
		# Verify for order node
		if not hasattr(root, 'order'):
			# Something went wrong
			raise Exception("Mollie returned errorcode {0}: {1}".format(root.item.errorcode, root.item.message))
		
		# Verify transaction_id
		if root.order.transaction_id.text != payment.transaction_id:
			raise Exception("Transaction id's did not match")
		
		# Verify order amount
		if root.order.amount != int(order.total.amount * 100):
			raise Exception("Order amount was not correctly transfered")
		
		# See if the order is payed and update order
		if root.order.payed:
			order.paid = order.total.amount
			order.save()
			status = self.MollieIdealPayment.SUCCESS
		else:
			status = self.MollieIdealPayment.FAILED
		
		# Complete the payment, successful or not
		payment.complete_transaction(status)
		
		return HttpResponse('')
		
	@view(r'^back$')
	def back(self, chain, request, **kwargs):
		transaction_id = request.GET.get('transaction_id', None)
		
		# Find a payment
		try:
			payment = self.MollieIdealPayment.objects.get(transaction_id=transaction_id)
		except self.MollieIdealPayment.DoesNotExist:
			raise Http404
		
		# Hand over to checkout process
		return redirect(reverse('checkout.checkout'))
			
	@view()
	def redirect(self, chain, request, order, **kwargs):
		
		settings = modules.payment.get_settings()
		
		payment = order.payment.downcast()
		payload = {
			'partnerid' : settings.mollie_partner_id,
			'amount' : int(order.total.amount * 100),
			'bank_id' : payment.bank_id,
			'description' : unicode(order),
			'reporturl' : request.build_absolute_uri(reverse('mollie_ideal.report')),
			'returnurl' : request.build_absolute_uri(reverse('mollie_ideal.back')),
		}
		
		if settings.test_mode:
			payload['testmode'] = 'true'
			
		if settings.mollie_profile_key:
			payload['profile_key'] = settings.mollie_profile_key,
		
		req = requests.get(self.mollie_fetch_url, params=payload)
		if req.status_code != requests.codes.ok:
			raise Exception()
		
		root = objectify.fromstring(req.text)
		
		# Verify for order node
		if not hasattr(root, 'order'):
			# Something went wrong
			raise Exception("Mollie returned errorcode {0}: {1}".format(root.item.errorcode, root.item.message))
		
		# Verify order amount
		if root.order.amount != int(order.total.amount * 100):
			raise Exception("Order amount was not correctly transfered")
			
		# Get the redirect url
		url = root.order.URL.text
		
		# Keep track of transaction id
		transaction_id = root.order.transaction_id.text
		payment.begin_transaction(transaction_id)
		
		if chain:
			return chain.execute(request=request, **kwargs)
		else:
			return redirect(url)
			
	@chainable()
	def get_bank_select_form(self, chain, prefix=None, data=None, form=None, bank=None, banks=None, **kwargs):
		if banks is None:
			banks = self.get_banks()
		if form is None:
			class BankSelectForm(self.BankSelectForm):
				bank = forms.ChoiceField(
					widget = forms.RadioSelect(),
					choices = [(bank[0], bank[1]) for bank in banks.values()]
				)
			initial = {}
			if bank:
				initial['bank'] = bank
			form = BankSelectForm(data, prefix=prefix, initial=initial)
		if chain:
			out = chain.execute(prefix=prefix, data=data, form=form, **kwargs)
			if out.has_key('form'):
				form = out['form']
		return form
			
	@chainable()
	def get_banks(self, chain):
		
		settings = modules.payment.get_settings()
		
		payload = {
			
		}
		
		if settings.test_mode:
			payload['testmode'] = 'true'
		
		req = requests.get(self.mollie_banklist_url, params=payload)
		root = objectify.fromstring(req.text)
		banks = {}
		for bank in root.iterchildren(tag='bank'):
			bank_id = str(bank.bank_id)
			banks[bank_id] = (bank_id, bank.bank_name)
		return banks
	
	@chainable()
	def handle_bank_select(self, chain, payment, prefix=None, data=None, bank=None, **kwargs):
		banks = self.get_banks()
		processed = False
		initial = None
		if not payment.bank_id is None:
			initial = payment.bank_id
		form = self.get_bank_select_form(prefix=prefix, data=data, banks=banks, bank=initial)
		if data and form.is_valid():
			# Resolve bank
			bank = form.cleaned_data['bank']
			bank = banks[str(bank)]
			payment.bank_id = bank[0].zfill(4)
			payment.bank_name = bank[1]
			processed = True
		if chain:
			return chain.execute(payment=payment, prefix=prefix, data=data, bank=bank, form=form, processed=processed, **kwargs)
		return bank, form, processed
	
	