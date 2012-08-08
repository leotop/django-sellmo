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
from sellmo.store.decorators import view, get

#

class StoreApp(sellmo.App):

	namespace = 'store'
	Purchase = models.Model

	def __init__(self, *args, **kwargs):
		from sellmo.api.store import Purchase
		self.Purchase = Purchase
			
	@get()
	def get_purchase_price(self, chain, purchase, **kwargs):
		price = apps.pricing.get_qty_price(item=purchase.product, qty=purchase.qty, **kwargs)
		if chain:
			out = chain.execute(price=price, purchase=purchase, **kwargs)
			assert out.has_key('price'), """Price not returned"""
			return out['price']
		else:
			return price
			
	@get(name='get_purchase')
	def make_purchase(self, chain, product, purchase=None, **kwargs):
		"""
		Creates a new store.Purchase, and saves it.
		"""
		if not purchase:
			purchase = self.Purchase(product=product)
			
		if chain:
			out = chain.execute(product=product, purchase=purchase, **kwargs)
			assert out.has_key('purchase'), """Purchase not returned"""
			purchase = out['purchase']
		
		purchase.save()
		return purchase
			