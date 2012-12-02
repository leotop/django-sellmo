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
from sellmo import apps
from sellmo.core.decorators import view, get

#

class PricingApp(sellmo.App):

	namespace = 'pricing'
	currency = 'EUR'
	types = []
	
	# Decimal field construction
	decimal_max_digits = 9
	decimal_places = 2
	stamped_decimal_max_digits = 15
	stamped_decimal_places = 8
	
	#
	
	class Stampable(models.Model):
		class Meta:
			abstract = True
	
	@staticmethod
	def construct_decimal_field(**kwargs):
		return models.DecimalField(
			max_digits = apps.pricing.decimal_max_digits,
			decimal_places = apps.pricing.decimal_places,
			**kwargs
		)
		
	#
	
	def __init__(self, *args, **kwargs):
		self.Stampable.add_to_class('amount', apps.pricing.construct_decimal_field())
		for type in self.types:
			self.Stampable.add_to_class('%s_amount' % type, self.construct_decimal_field())
			
	@get()
	def get_qty_price(self, chain, product, qty=1, price=None, **kwargs):
		if chain:
			out = chain.execute(product=product, qty=qty, price=price, **kwargs)
			if not out.has_key('price'):
				raise Exception("""Price not returned""")
			price = out['price']
		
		return price
			
	