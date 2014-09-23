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

from sellmo.api.checkout.process import CheckoutProcess, CheckoutStep


class MollieStepBase(CheckoutStep):
    
    invalid_context = None
    view = None
    
    def __init__(self, order, request, next_step):
        super(MollieStepBase, self).__init__(order=order, request=request)
        self.next_step = next_step
        self.payment = self.order.payment.downcast()
        
    def complete(self, data):
        self.invalid_context = {}
        return self.contextualize_or_complete(self.request,
                                              self.invalid_context, data)
    
    def render(self, request, context):
        if self.invalid_context is None:
            self.contextualize_or_complete(request, context)
        else:
            context.update(self.invalid_context)
    
        view = getattr(modules.mollie, self.view)
        return view(request=request, order=self.order, context=context)
        
    def contextualize_or_complete(self, request, context, data=None):
        pass

class MollieIdealIssuerSelectStep(MollieStepBase):
    
    key = 'ideal_issuer_select'
    view = 'ideal_issuer_select'
    
    def is_completed(self):
        return bool(self.payment.issuer)

    def can_skip(self):
        return False

    def get_next_step(self):
        return MollieRedirectStep(order=self.order, request=self.request, 
                                  next_step=self.next_step)

    def contextualize_or_complete(self, request, context, data=None):
        success = True

        bank, form, processed = modules.mollie.process_ideal_issuer_select(
            request=request, payment=self.payment, 
            prefix='issuer_select', data=data)
        context['issuer_select_form'] = form
        success &= processed
        
        if data is not None and success:
            self.payment.save()

        return success


class MollieRedirectStep(MollieStepBase):
    
    key = 'mollie_redirect'
    view = 'redirect'
    
    def is_completed(self):
        return False

    def can_skip(self):
        return False

    def get_next_step(self):
        return None


class MolliePendingStep(MollieStepBase):
    
    key = 'mollie_pending'
    view = 'pending'
    
    def has_deviated(self):
        return True

    def is_completed(self):
        return not self.payment.is_pending

    def can_skip(self):
        return False

    def get_next_step(self):
        return False

    def contextualize_or_complete(self, request, context, data=None):
        success = True
        
        if data and 'pay_again' in data:
            self.payment.reset_transaction()

        return success


class MollieFailureStep(MollieStepBase):
    
    key = 'mollie_failure'
    view = 'failure'

    def has_deviated(self):
        return True

    def is_completed(self):
        return not self.payment.has_transaction

    def can_skip(self):
        return False

    def get_next_step(self):
        return False

    def contextualize_or_complete(self, request, context, data=None):
        success = True
        
        if data and 'pay_again' in data:
            self.payment.reset_transaction()

        return success
