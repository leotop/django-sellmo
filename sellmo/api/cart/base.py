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

from sellmo import apps
from sellmo.api.pricing import Price

#

_session_key = 'sellmo_cart'

class Cart(object):
		
	@staticmethod
	def exists(request):
		return request.session.get(_session_key, False) != False
		
	def __init__(self, request):
		if Cart.exists(request):
			self._existing(request)
		else:
			self._new(request)
			
	def _new(self, request):
		self.cart = apps.cart.Cart()
		self.cart.save()
		request.session[_session_key] = self.cart.id
		
	def _existing(self, request):
		try:
			self.cart = apps.cart.Cart.objects.get(id=request.session.get(_session_key))
		except apps.cart.Cart.DoesNotExist:
			self._new(request)
			
	def add(self, purchase):
		purchase.save()
		item = apps.cart.CartItem(cart=self.cart, purchase=purchase)
		item.save()
		
	def remove(self, purchase):
		pass
		
	def clear(self):
		pass
	
	def __iter__(self):
		for item in self.cart.items.all():
			yield item
			
	# Pricing
	@property
	def total(self):
		price = Price()
		for item in self:
			price += item.total
		return price