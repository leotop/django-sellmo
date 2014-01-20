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
from sellmo.contrib.contrib_payment.methods.ideal.mollie_ideal import MollieIdealPaymentMethod

#

from django.db import models
from django.utils.translation import ugettext_lazy as _

#
	
@load(action='finalize_mollie_ideal_Payment', after='finalize_checkout_Payment')
def finalize_model():
	
	class MollieIdealPayment(modules.checkout.Payment, modules.mollie_ideal.MollieIdealPayment):
		
		def get_method(self):
			return MollieIdealPaymentMethod()
			
		def __unicode__(self):
			return unicode(self.get_method())
		
		class Meta:
			app_label = 'checkout'
			verbose_name = _("mollie ideal payment")
			verbose_name_plural = _("mollie ideal payments")
		
	modules.mollie_ideal.MollieIdealPayment = MollieIdealPayment

	
class MollieIdealPayment(models.Model):
	
	SUCCESS = 10
	FAILED = 20
	EXPIRED = 30
	CANCELED = 40
	
	STATUS_CODES = (
		(SUCCESS, _("success")),
		(FAILED, _("failed")),
		(EXPIRED, _("expired")),
		(CANCELED, _("canceled")),
	)
	
	bank_id = models.CharField(
		max_length = 4,
		editable = False,
	)
	
	bank_name = models.CharField(
		max_length = 255,
		editable = False,
	)
	
	def begin_transaction(self, transaction_id, save=True):
		self.transaction_id = transaction_id
		self.transaction_status = None
		self.transaction_report = False
		if save:
			self.save()
		
	def abort_transaction(self, save=True):
		self.transaction_id = ''
		self.transaction_status = None
		self.transaction_report = False
		if save:
			self.save()
		
	def retry(self, save=True):
		self.abort_transaction()
		self.bank_id = ''
		self.bank_name
		if save:
			self.save()
			
	def complete_transaction(self, status, save=True):
		self.transaction_status = status
		self.transaction_report = True
		if save:
			self.save()
	
	transaction_id = models.CharField(
		max_length = 32,
		editable = False,
	)
	
	transaction_report = models.BooleanField(
		default = False,
		editable = False
	)
	
	transaction_status = models.PositiveIntegerField(
		null = True,
		editable = False,
		choices = STATUS_CODES
	)
	
	@property
	def is_pending(self):
		if self.transaction_id and not self.transaction_report:
			return True
		return False
		
	@property
	def is_success(self):
		return self.transaction_status == self.SUCCESS
		
	@property
	def is_completed(self):
		return not self.transaction_status is None
	
	class Meta:
		abstract = True
		
