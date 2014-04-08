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
from sellmo.api.pricing import Price
from sellmo.api.checkout import PaymentMethod

from sellmo.api.checkout.process import CheckoutProcess, CheckoutStep


class MollieIdealBankSelectStep(CheckoutStep):

    invalid_context = None
    key = 'ideal_bank_select'

    def __init__(self, order, request, next_step):
        super(MollieIdealBankSelectStep, self).__init__(
            order=order, request=request)
        self.next_step = next_step
        self.payment = self.order.payment.downcast()

    def is_completed(self):
        return self.payment.bank_id

    def can_skip(self):
        return False

    def get_next_step(self):
        return MollieIdealRedirectStep(
            order=self.order, request=self.request, next_step=self.next_step)

    def _contextualize_or_complete(self, request, context, data=None):
        success = True

        bank, form, processed = modules.mollie_ideal.process_bank_select(
            request=request, payment=self.payment, 
            prefix='bank_select', data=data)
        context['bank_select_form'] = form
        success &= processed

        if data is not None and success:
            self.payment.save()

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

        return modules.mollie_ideal.bank_select(
            request=request, order=self.order, context=context)


class MollieIdealRedirectStep(CheckoutStep):

    invalid_context = None
    key = 'ideal_redirect'

    def __init__(self, order, request, next_step):
        super(MollieIdealRedirectStep, self).__init__(
            order=order, request=request)
        self.next_step = next_step

    def is_completed(self):
        return False

    def can_skip(self):
        return False

    def get_next_step(self):
        return None

    def render(self, request, context):
        return modules.mollie_ideal.redirect(
            request=request, order=self.order, contex=context)


class MollieIdealPendingStep(CheckoutStep):

    invalid_context = None
    key = 'ideal_pending'

    def __init__(self, order, request, next_step):
        super(MollieIdealPendingStep, self).__init__(
            order=order, request=request)
        self.next_step = next_step
        self.payment = self.order.payment.downcast()

    def has_deviated(self):
        return True

    def is_completed(self):
        return not self.payment.is_pending

    def can_skip(self):
        return False

    def get_next_step(self):
        return False

    def _contextualize_or_complete(self, request, context, data=None):
        success = True

        if data and 'pay_again' in data:
            self.payment.retry()

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

        return modules.mollie_ideal.pending(
            request=request, order=self.order, context=context)


class MollieIdealFailureStep(CheckoutStep):

    invalid_context = None
    key = 'ideal_failure'

    def __init__(self, order, request, next_step):
        super(MollieIdealFailureStep, self).__init__(
            order=order, request=request)
        self.next_step = next_step
        self.payment = self.order.payment.downcast()

    def has_deviated(self):
        return True

    def is_completed(self):
        return not self.payment.transaction_status is False

    def can_skip(self):
        return False

    def get_next_step(self):
        return False

    def _contextualize_or_complete(self, request, context, data=None):
        success = True

        if data and 'pay_again' in data:
            self.payment.retry()

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

        return modules.mollie_ideal.failure(
            request=request, order=self.order, context=context)
