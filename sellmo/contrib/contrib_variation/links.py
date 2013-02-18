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

#

from sellmo import modules
from sellmo.api.decorators import link

#

from django import forms
from django.forms.formsets import formset_factory

@link(namespace=modules.cart.namespace)
def get_add_to_cart_formset(formset, cls, product, initial=None, data=None, **kwargs):
	
	# Before proceeding to custom form creation, check if we're dealing with a variation product
	if not product.variations and (not modules.variation.custom_options_enabled or not product.custom_options):
		return
	
	class AddToCartForm(cls):
		if product.variations and not modules.variation.batch_buy_enabled:
			variation = forms.ChoiceField(
				choices = [(variation.hash, unicode(variation)) for variation in product.variations]
			)
	
	AddToCartFormSet = formset_factory(AddToCartForm, extra=0)
	
	if not data:
		if product.variations:
			if not modules.variation.batch_buy_enabled:
				for el in initial:
					el['variation'] = product.variations[:1][0].hash
			else:
				initial = [{
					'variation' : variation.hash,
					'qty' : 1
				} for variation in product.variations]
				
		formset = AddToCartFormSet(initial=initial)
	else:
		formset = AddToCartFormSet(data)
		
	return {
		'formset' : formset
	}