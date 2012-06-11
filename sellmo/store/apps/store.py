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
		
	@view()
	def on_view(self, chain, request, context=None, **kwargs):
		if context == None:
			context = {}
	
		if chain:
			chain.execute(request, context=context, **kwargs)
			
	@view()
	def on_purchase(self, chain, request, purchase, **kwargs):
		if chain:
			chain.execute(request, purchase=purchase, **kwargs)
			
	@get()
	def get_price(self, chain, purchase, item=None, **kwargs):
		if not item:
			item = purchase.variant if purchase.variant else purchase.product
		price = apps.pricing.get_qty_price(item=item, qty=purchase.qty, **kwargs)
		if chain:
			out = chain.execute(price=price, purchase=purchase, **kwargs)
			assert out.has_key('price'), """Price not returned"""
			return out['price']
		else:
			return price