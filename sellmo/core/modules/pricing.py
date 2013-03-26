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

#

import sellmo
from sellmo import modules
from sellmo.api.decorators import view, chainable, load
from sellmo.api.pricing import Price
from sellmo.api.pricing.models import Stampable

#

@load(after='load_pricing_Stampable', before='finalize_pricing_Stampable')
def load_model():
	modules.pricing.Stampable.add_to_class('amount', modules.pricing.construct_decimal_field())
	for type in modules.pricing.types:
		modules.pricing.Stampable.add_to_class('%s_amount' % type, modules.pricing.construct_decimal_field())

class PricingModule(sellmo.Module):
	"""
	Routes product pricing logic to higher level modules and acts as a container for pricing
	related models.
	"""

	namespace = 'pricing'
	currency = 'EUR'
	types = []
	Stampable = Stampable
	
	#: Configures the max digits for a pricing (decimal) field
	decimal_max_digits = 9
	#: Configures the amount of decimal places for a pricing (decimal) field
	decimal_places = 2
	
	@staticmethod
	def construct_decimal_field(**kwargs):
		"""
		Constructs a decimal field. 
		"""
		return models.DecimalField(
			max_digits = modules.pricing.decimal_max_digits,
			decimal_places = modules.pricing.decimal_places,
			**kwargs
		)
	
	def __init__(self, *args, **kwargs):
		pass
			
	@chainable()
	def stamp(self, chain, stampable, price, **kwargs):
		stampable.amount = price.amount
		for type in self.types:
			attr = '%s_amount' % type
			setattr(stampable, attr, price[type].amount)
			
	@chainable()
	def get_price(self, chain, product, price=None, **kwargs):
		if chain:
			out = chain.execute(product=product, price=price, **kwargs)
			if out.has_key('price'):
				price = out['price']
		
		# Ensure we're dealing with a number
		if not isinstance(price, Price):
			raise Exception("An invalid 'price' was provided")
		
		return price
	