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

#

from django.db import models
from django.contrib.sites.models import Site
from django.utils.translation import ugettext_lazy as _

#

@load(before='finalize_checkout_mailing_OrderMail')
@load(after='finalize_checkout_Order')
@load(after='finalize_mailing_MailStatus')
def load_model():
	class OrderMail(modules.checkout_mailing.OrderMail):
		
		order = models.ForeignKey(
			modules.checkout.Order,
			editable = False,
		)
		
		status = models.ForeignKey(
			modules.mailing.MailStatus,
			editable = False,
		)
		
		class Meta(modules.checkout_mailing.OrderMail.Meta):
			abstract = True
	
	modules.checkout_mailing.OrderMail = OrderMail
	
@load(action='finalize_checkout_mailing_OrderMail')
def finalize_model():
	class OrderMail(modules.checkout_mailing.OrderMail):
		class Meta(modules.checkout_mailing.OrderMail.Meta):
			app_label = 'checkout'
			verbose_name = _("order mail")
			verbose_name_plural = _("order mails")

	modules.checkout_mailing.OrderMail = OrderMail

class OrderMail(models.Model):
	
	class Meta:
		abstract = True
