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
from sellmo.contrib.contrib_payment.methods.cash_payment import CashPaymentMethod

#

from django.db import models
from django.utils.translation import ugettext_lazy as _

#

@load(action='finalize_cash_payment_Payment', after='finalize_checkout_Payment')
def finalize_model():

	class CashPayment(modules.checkout.Payment, modules.cash_payment.CashPayment):
		
		instant = False
		
		def get_method(self):
			return CashPaymentMethod()
			
		def __unicode__(self):
			return unicode(self.get_method())
		
		class Meta:
			app_label = 'checkout'
			verbose_name = _("cash payment")
			verbose_name_plural = _("cash payments")

	modules.cash_payment.CashPayment = CashPayment

@load(before='finalize_payment_PaymentSettings')
def finalize_model():

	class PaymentSettings(modules.payment.PaymentSettings):
		
		cash_payment_description = models.CharField(
			max_length = 80,
			default = _("cash payment"),
			verbose_name = _("cash payment description")
		)
		
		cash_payment_additional_text = models.TextField(
			blank = True,
			verbose_name = _("cash payment additional text")
		)
		
		class Meta:
			abstract = True

	modules.payment.PaymentSettings = PaymentSettings

class CashPayment(models.Model):
	
	class Meta:
		abstract = True
		
