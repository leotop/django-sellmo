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

from sellmo import modules
from sellmo.api.pricing import Price
from sellmo.api.checkout import ShippingMethod

#

from django.utils.translation import ugettext_lazy as _

#

class TieredShippingMethod(ShippingMethod):
	
	identifier = None
	name = None
	
	def new_shipment(self, order):
		return modules.shipping.Shipment(
			method=self.method,
			carrier=self.carrier,
		)

	def __init__(self, identifier, name, method, carrier=None):
		self.identifier = identifier
		self.name = name
		self.method = method
		self.carrier = carrier
		
	def is_available(self, order, **kwargs):
		try:
			costs = self.method.tiers.for_order(order).costs
		except modules.shipping.TieredShippingTier.DoesNotExist:
			return False
		return True

	def get_costs(self, order, currency=None, **kwargs):
		costs = 0
		try:
			costs = self.method.tiers.for_order(order).costs
		except modules.shipping.TieredShippingTier.DoesNotExist:
			raise Exception(_("Cannot get shipping costs for this order"))
			
		if self.carrier:
			costs += self.carrier.extra_costs
		return modules.pricing.get_price(price=Price(costs), shipping_method=self)