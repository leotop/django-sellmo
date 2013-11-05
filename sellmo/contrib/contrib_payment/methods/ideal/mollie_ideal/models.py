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
from sellmo.api.decorators import load
from sellmo.api.pricing import Price
from sellmo.contrib.contrib_payment.methods.ideal.mollie_ideal import MollieIdealPaymentMethod as _MollieIdealPaymentMethod

#

from django.db import models
from django.utils.translation import ugettext_lazy as _

#

@load(action='load_payment_subtypes', after='finalize_payment_PaymentMethod')
def load_payment_subtypes():

	class MollieIdealPaymentMethod(modules.payment.PaymentMethod):

		costs = modules.pricing.construct_pricing_field(
			verbose_name = _("payment costs"),
		)

		def get_method(self, carrier=None):
			identifier = self.identifier
			return _MollieIdealPaymentMethod(identifier, self.description, method=self)

		class Meta:
			app_label = 'payment'
			verbose_name = _("mollie ideal payment method")
			verbose_name_plural = _("mollie ideal payment methods")

	modules.payment.register_subtype(MollieIdealPaymentMethod)
	
@load(action='finalize_mollie_ideal_Payment', after='finalize_checkout_Payment')
def finalize_model():
	
	class MollieIdealPayment(modules.checkout.Payment, modules.mollie_ideal.MollieIdealPayment):
		class Meta:
			app_label = 'checkout'
			verbose_name = _("mollie ideal payment")
			verbose_name_plural = _("mollie ideal payments")
		
	modules.mollie_ideal.MollieIdealPayment = MollieIdealPayment
	
class MollieIdealPayment(models.Model):
	
	bank_id = models.PositiveIntegerField(
		blank = True,
		null = True
	)
	
	bank_name = models.CharField(
		max_length = 255,
		blank = True
	)
	
	class Meta:
		abstract = True
	
# Init modules
from sellmo.contrib.contrib_payment.methods.ideal.mollie_ideal.modules import *