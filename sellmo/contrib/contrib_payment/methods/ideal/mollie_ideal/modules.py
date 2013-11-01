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

from django.http import Http404
from django import forms

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
	def redirect(self, chain, order, **kwargs):
		
		payment = order.payment.downcast()
		payload = {
			'partnerid' : '0',
			'amount' : '1000',
			'bank_id' : payment.bank_id,
			'description' : 'ordernummer',
			'returnurl' : 'aaa',
		}
		
		req = requests.get(self.mollie_fetch_url, params=payload)
		if req.status_code != requests.codes.ok:
			raise Exception("Errr")
		
		print req.text
		
		if chain:
			return chain.execute(request=request, **kwargs)
		else:
			return None
			
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
		req = requests.get(self.mollie_banklist_url)
		root = objectify.fromstring(req.text)
		banks = {}
		for bank in root.iterchildren(tag='bank'):
			banks[str(bank.bank_id)] = (bank.bank_id, bank.bank_name)
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
			payment.bank_id = bank[0]
			payment.bank_name = bank[1]
			processed = True
		if chain:
			return chain.execute(payment=payment, prefix=prefix, data=data, bank=bank, form=form, processed=processed, **kwargs)
		return bank, form, processed
	
	