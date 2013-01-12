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
from sellmo.api.checkout import ShippingMethod

#

from django.db import models
from django.utils.translation import ugettext_lazy as _

#

class Method(models.Model):

	carrier = models.CharField(
		max_length = 30,
	)
	
	description = models.TextField(
		blank = True,
		null = True
	)
	
	def to_sellmo_method(self):
		raise NotImplementedError()

	class Meta:
		abstract = True

#

class BasicMethod(Method):

	def to_sellmo_method(self):
		return ShippingMethod(self.carrier, description=self.description)

	class Meta:
		app_label = 'shipping'
		verbose_name = _("basic shipping method")
		verbose_name_plural = _("basic shipping methods")

#

class TieredMethod(Method):

	def to_sellmo_method(self):
		return ShippingMethod(self.carrier, description=self.description)

	class Meta:
		app_label = 'shipping'
		verbose_name = _("tiered shipping method")
		verbose_name_plural = _("tiered shipping methods")

class TieredMethodTier(models.Model):
	
	method = models.ForeignKey(
		TieredMethod
	)
	
	#
	amount = modules.pricing.construct_decimal_field()
	tier = modules.pricing.construct_decimal_field()
	
	class Meta:
		app_label = 'shipping'
		verbose_name = _("shipping tier")
		verbose_name_plural = _("shipping tiers")