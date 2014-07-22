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


from sellmo import modules
from sellmo.api.pricing import Price
from sellmo.api.checkout import PaymentMethod
from sellmo.contrib.payment.methods \
        .mollie.process import (MollieRedirectStep,
                                MolliePendingStep,
                                MollieFailureStep,
                                MollieIdealIssuerSelectStep)

from django.utils.translation import ugettext_lazy as _


class MolliePaymentMethod(PaymentMethod):
    
    def __init__(self, identifier, name=None):
        if name is None:
            name = identifier
        self.identifier = identifier
        self.name = name
    
    def process(self, order, request, next_step):
        if order.payment.is_paid:
            return next_step
        elif order.payment.is_expired or order.payment.is_cancelled:
            return self.process_failure(order, request, next_step)
        elif order.payment.is_pending or order.payment.is_open:
            return self.process_pending(order, request, next_step)
        else:
            return self.process_unpaid(order, request, next_step)
        
    def process_unpaid(self, order, request, next_step):
        return MollieRedirectStep(order=order, request=request,
                                  next_step=next_step)
                                  
    def process_failure(self, order, request, next_step):
        return MollieFailureStep(order=order, request=request,
                                 next_step=next_step)
                                  
    def process_pending(self, order, request, next_step):
        return MolliePendingStep(order=order, request=request,
                                 next_step=next_step)
    
    def new_payment(self, order):
        return modules.mollie.MolliePayment(method=self.identifier)
        
    def get_mollie_kwargs(self, order):
        return {
            'method': order.payment.method,
        }

    def get_costs(self, order, currency=None, **kwargs):
        return modules.pricing.get_price(price=Price(0), payment_method=self)
    
    def __unicode__(self):
        return self.name


class MollieIDealPaymentMethod(MolliePaymentMethod):
    
    def get_mollie_kwargs(self, order):
        kwargs = super(MollieIDealPaymentMethod, self).get_mollie_kwargs(order)
        return dict(kwargs, **{
            'issuer': order.payment.issuer,
        })
    
    def process_unpaid(self, order, request, next_step):
        return MollieIdealIssuerSelectStep(order=order, request=request, 
                                           next_step=next_step)
    
    
        
