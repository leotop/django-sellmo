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
from sellmo.api.checkout.process import CheckoutProcess, CheckoutStep
from sellmo.contrib.contrib_checkout.forms import AcceptTermsForm
from sellmo.contrib.contrib_checkout.config import settings as checkout_settings
from sellmo.config import settings

#

class MultiStepCheckoutProcess(CheckoutProcess):
    
    def get_first_step(self):
        if not settings.AUTH_ENABLED or self.order.email:
            key = 'information'
            step = InformationStep(order=self.order, request=self.request)
        else:
            key = 'login'
            step = LoginStep(order=self.order, request=self.request)
        return modules.multistep_checkout.get_step(key=key, order=self.order, request=self.request, step=step)
    
class LoginStep(CheckoutStep):
    
    invalid_context = None
    key = 'login'
    
    def is_definitive(self):
        return self.order.is_pending
    
    def is_completed(self):
        return self.request.user.is_authenticated()
        
    def can_skip(self):
        return True
        
    def get_next_step(self):
        step = InformationStep(order=self.order, request=self.request)
        return modules.multistep_checkout.get_step(key='information', order=self.order, request=self.request, step=step)
        
    def contextualize_or_complete(self, request, context, data=None, success=True):
        user, form, processed = modules.customer.handle_login(request=request, prefix='login', data=data)
        context['login_form'] = form
        success &= processed
        
        if success:
            modules.customer.login_user(request=request, user=user)
        
        return success
        
    def complete(self, data):
        self.invalid_context = {}
        return self.contextualize_or_complete(self.request, self.invalid_context, data)
        
    def render(self, request, context):
        if self.invalid_context is None:
            self.contextualize_or_complete(request, context)
        else:
            context.update(self.invalid_context)
        return modules.multistep_checkout.login(request=request, context=context)
        
class InformationStep(CheckoutStep):
    
    invalid_context = None
    key = 'information'
    
    def is_completed(self):
        for type in settings.ADDRESS_TYPES:
            if self.order.get_address(type) is None:
                return False    
        if self.order.needs_shipping and self.order.shipment is None:
            return False
        return True
        
    def is_definitive(self):
        return self.order.is_pending
        
    def get_next_step(self):
        step = PaymentMethodStep(order=self.order, request=self.request)
        next_step = modules.multistep_checkout.get_step(key='payment_method', order=self.order, request=self.request, step=step)
        if self.order.needs_shipping:
            return self.order.shipment.get_method().process(request=self.request, order=self.order, next_step=next_step)
        else:
            return next_step
        
    def contextualize_or_complete(self, request, context, data=None, success=True):
        addresses = {}
        
        contactable, form, processed = modules.customer.handle_contactable(prefix='contactable', contactable=self.order, data=data)
        context['contactable_form'] = form
        success &= processed
        
        if self.order.needs_shipping:
            method, form, processed = modules.checkout.handle_shipping_method(order=self.order, prefix='shipping_method', data=data)
            context['shipping_method_form'] = form
            success &= processed
        
        for type in settings.ADDRESS_TYPES:
            address, form, processed = modules.customer.handle_address(type=type, prefix='{0}_address'.format(type), address=self.order.get_address(type), data=data)
            context['{0}_address_form'.format(type)] = form
            success &= processed
            addresses[type] = address
        
        if data is not None and success:
            for type in settings.ADDRESS_TYPES:
                address = addresses[type]
                address.save()
                self.order.set_address(type, address)
            self.order.save()
        
        return success
        
    def complete(self, data):
        self.invalid_context = {}
        return self.contextualize_or_complete(self.request, self.invalid_context, data)
        
    def render(self, request, context):
        if self.invalid_context is None:
            self.contextualize_or_complete(request, context)
        else:
            context.update(self.invalid_context)
        
        return modules.multistep_checkout.information(request=request, context=context)
        
class PaymentMethodStep(CheckoutStep):

    invalid_context = None
    key = 'payment_method'

    def is_completed(self):
        if self.order.payment is None:
            return False
        return True
        
    def is_definitive(self):
        return self.order.is_pending
        
    def get_next_step(self):
        step = SummaryStep(order=self.order, request=self.request)
        return modules.multistep_checkout.get_step(key='summary', order=self.order, request=self.request, step=step)

    def contextualize_or_complete(self, request, context, data=None, success=True):
        method, form, processed = modules.checkout.handle_payment_method(order=self.order, prefix='payment_method', data=data)
        context['payment_method_form'] = form
        success &= processed

        if data is not None and success:
            self.order.save()
        
        return success

    def complete(self, data):
        self.invalid_context = {}
        return self.contextualize_or_complete(self.request, self.invalid_context, data)

    def render(self, request, context):
        if self.invalid_context is None:
            self.contextualize_or_complete(request, context)
        else:
            context.update(self.invalid_context)
        return modules.multistep_checkout.payment_method(request=request, context=context)
        
class SummaryStep(CheckoutStep):
    
    invalid_context = None
    key = 'summary'
    
    def is_completed(self):
        return self.order.is_pending
        
    def is_definitive(self):
        return True
        
    def get_next_step(self):
        return self.order.payment.get_method().process(request=self.request, order=self.order, next_step=None)
    
    def contextualize_or_complete(self, request, context, data=None, success=True):
        if checkout_settings.ACCEPT_TERMS_ENABLED:
            form = AcceptTermsForm(data, prefix='accept_terms')
            context['accept_terms_form'] = form
            if data:
                success &= form.is_valid()
            else:
                success = False
        
        if data is not None and success:
            self.order.place()
        return success
    
    def complete(self, data):
        self.invalid_context = {}
        return self.contextualize_or_complete(self.request, self.invalid_context, data)
    
    def render(self, request, context):
        if self.invalid_context is None:
            self.contextualize_or_complete(request, context)
        else:
            context.update(self.invalid_context)
        
        return modules.multistep_checkout.summary(request=request, context=context)
    