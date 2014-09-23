# Copyright (c) 2014, Adaptiv Design
# All rights reserved.
# 
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:

# 1. Redistributions of source code must retain the above copyright notice,
# this list of conditions and the following disclaimer.

# 2. Redistributions in binary form must reproduce the above copyright notice,
# this list of conditions and the following disclaimer in the documentation
# and/or other materials provided with the distribution.

# 3. Neither the name of the copyright holder nor the names of its contributors
# may be used to endorse or promote products derived from this software without
# specific prior written permission.

# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
# ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE
# LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR
# CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF
# SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS
# INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN
# CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)
# ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
# POSSIBILITY OF SUCH DAMAGE.


import uuid

from sellmo import modules
from sellmo.api.decorators import load
from sellmo.contrib.payment.methods.mollie.utils import fix_amount

from django.db import models
from django.utils.translation import ugettext_lazy as _


import Mollie


@load(action='finalize_mollie_MolliePayment')
@load(after='finalize_checkout_Payment')
def finalize_model():

    class MolliePayment(
            modules.checkout.Payment,
            modules.mollie.MolliePayment):

        def get_method(self):
            return modules.mollie.get_methods()[self.method]

        def __unicode__(self):
            return unicode(self.get_method())

        class Meta(modules.mollie.MolliePayment.Meta):
            app_label = 'checkout'

    modules.mollie.MolliePayment = MolliePayment


class MolliePayment(models.Model):
    
    method = models.CharField(
        max_length=20,
        editable=False,
    )
    
    issuer = models.CharField(
        max_length=40,
        editable=False,
    )
    
    status = models.CharField(
        max_length=20,
        editable=False,
    )
    
    internal_id = models.CharField(
        max_length=32,
        db_index=True,
        editable=False,
    )
    
    external_id = models.CharField(
        max_length=32,
        db_index=True,
        editable=False,
    )
    
    def new_transaction(self, internal_id, payment):
        self.internal_id = internal_id
        self.external_id = payment['id']
        self.update_transaction(payment)
        
    def update_transaction(self, payment):
        if self.status != payment['status']:
            self.status = payment['status']
            a = fix_amount(self.order.total.amount)
            b = fix_amount(payment['amount'])
            if self.is_paid:
                # Sanity check
                if a != b:
                    raise Exception("Payment amount '{0}' is invalid."
                                    .format(payment['amount']))
                self.order.paid = self.order.total.amount
                self.order.save()
        self.save()
        
    def reset_transaction(self):
        self.internal_id = ''
        self.external_id = ''
        self.status = ''
        self.save()
        
    @property
    def has_transaction(self):
        return bool(self.internal_id)
    
    @property
    def is_open(self):
        return self.status == Mollie.API.Object.Payment.STATUS_OPEN
        
    @property
    def is_pending(self):
        return self.status == Mollie.API.Object.Payment.STATUS_PENDING
    
    @property
    def is_expired(self):
        return self.status == Mollie.API.Object.Payment.STATUS_EXPIRED
        
    @property
    def is_cancelled(self):
        return self.status == Mollie.API.Object.Payment.STATUS_CANCELLED
        
    @property
    def is_paid(self):
        return self.status == Mollie.API.Object.Payment.STATUS_PAID
        
    @property
    def is_paidout(self):
        return self.status == Mollie.API.Object.Payment.STATUS_PAIDOUT
        
    @property
    def is_refunded(self):
        return self.status == Mollie.API.Object.Payment.STATUS_REFUNDED

    class Meta:
        abstract = True
        verbose_name = _("mollie payment")
        verbose_name_plural = _("mollie payments")
    
