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
from sellmo.api.checkout.process import CheckoutProcess, CheckoutStep
from sellmo.contrib.contrib_checkout \
           .forms import AcceptTermsForm


class MultiStepCheckoutProcess(CheckoutProcess):

    def get_first_step(self):
        step = InformationStep(order=self.order, request=self.request)
        return modules.checkout.get_checkout_step(
            key='information', order=self.order, 
            request=self.request, step=step)


class InformationStep(CheckoutStep):

    invalid_context = None
    key = 'information'

    def is_completed(self):
        for type in modules.customer.address_types:
            if self.order.get_address(type) is None:
                return False
        if self.order.needs_shipping and self.order.shipment is None:
            return False
        return True

    def is_definitive(self):
        return self.order.is_pending

    def get_next_step(self):
        step = PaymentMethodStep(order=self.order, request=self.request)
        next_step = modules.checkout.get_checkout_step(
            key='payment_method', order=self.order,
            request=self.request, step=step)
        if self.order.needs_shipping:
            return self.order.shipment.get_method().process(
                request=self.request, order=self.order,
                next_step=next_step)
        else:
            return next_step

    def contextualize_or_complete(self, request, context, data=None,
                                  success=True):
        addresses = {}

        contactable, form, processed = modules.customer.process_contactable(
            request=request, prefix='contactable',
            contactable=self.order, data=data)
        context['contactable_form'] = form
        success &= processed

        if self.order.needs_shipping:
            method, form, processed = modules.checkout.process_shipping_method(
                request=request, order=self.order,
                prefix='shipping_method', data=data)
            context['shipping_method_form'] = form
            success &= processed

        for type in modules.customer.address_types:
            address, form, processed = modules.customer.process_address(
                request=request, type=type,
                prefix='{0}_address'.format(type),
                address=self.order.get_address(type), data=data)
            context['{0}_address_form'.format(type)] = form
            success &= processed
            addresses[type] = address

        if data is not None and success:
            for type in modules.customer.address_types:
                address = addresses[type]
                address.save()
                self.order.set_address(type, address)
            self.order.save()

        return success

    def complete(self, data):
        self.invalid_context = {}
        return self.contextualize_or_complete(
            self.request, self.invalid_context, data)

    def render(self, request, context):
        if self.invalid_context is None:
            self.contextualize_or_complete(request, context)
        else:
            context.update(self.invalid_context)

        return modules.checkout.information_step(
            request=request, context=context)


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
        return modules.checkout.get_checkout_step(
            key='summary', order=self.order,
            request=self.request, step=step)

    def contextualize_or_complete(self, request, context, data=None, 
                                  success=True):
        method, form, processed = modules.checkout.process_payment_method(
            request=request, order=self.order, 
            prefix='payment_method', data=data)
        context['payment_method_form'] = form
        success &= processed

        if data is not None and success:
            self.order.save()

        return success

    def complete(self, data):
        self.invalid_context = {}
        return self.contextualize_or_complete(
            self.request, self.invalid_context, data)

    def render(self, request, context):
        if self.invalid_context is None:
            self.contextualize_or_complete(request, context)
        else:
            context.update(self.invalid_context)
        return modules.checkout.payment_method_step(
            request=request, context=context)


class SummaryStep(CheckoutStep):

    invalid_context = None
    key = 'summary'

    def is_completed(self):
        return self.order.is_pending

    def is_definitive(self):
        return True

    def get_next_step(self):
        return self.order.payment.get_method().process(
            request=self.request, order=self.order, next_step=None)

    def contextualize_or_complete(self, request, context, data=None,
                                  success=True):
        if modules.checkout.accept_terms_enabled:
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
        return self.contextualize_or_complete(
            self.request, self.invalid_context, data)

    def render(self, request, context):
        if self.invalid_context is None:
            self.contextualize_or_complete(request, context)
        else:
            context.update(self.invalid_context)

        return modules.checkout.summary_step(
            request=request, context=context)
