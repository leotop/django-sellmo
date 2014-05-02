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
from sellmo.api.checkout.process import CheckoutStep


class CheckoutLoginStep(CheckoutStep):
    
    key = 'login'
    invalid_context = None
    
    def __init__(self, order, request, next_step):
        super(CheckoutLoginStep, self).__init__(order, request)
        self.next_step = next_step
    
    def get_next_step(self):
        return self.next_step
    
    def is_definitive(self):
        return self.order.is_pending
    
    def is_completed(self):
        if self.order.pk is None:
            customer = modules.customer.get_customer(request=self.request)
            return customer is not None and customer.is_authenticated()
        return True
    
    def can_skip(self):
        return True
        
    def _contextualize_or_complete(self, request, context, data=None):
        success = True
    
        user, form, processed = modules.account.process_login(
            request=request, prefix='login', data=data)
        context['login_form'] = form
        success &= processed
    
        return success
    
    def complete(self, data):
        self.invalid_context = {}
        return self._contextualize_or_complete(
            self.request, self.invalid_context, data)
    
    def render(self, request, context):
        if self.invalid_context is None:
            self._contextualize_or_complete(request, context)
        else:
            context.update(self.invalid_context)
    
        return modules.checkout.login_step(request=request, context=context)