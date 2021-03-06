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


from django import forms, dispatch
from django.http import Http404
from django.core.urlresolvers import reverse
from django.core.exceptions import ImproperlyConfigured
from django.shortcuts import redirect
from django.db import models, transaction
from django.utils.decorators import method_decorator
from django.utils.translation import ugettext_lazy as _

import sellmo
from sellmo import modules
from sellmo.core.processing import ProcessError
from sellmo.utils.tracking import UntrackableError
from sellmo.utils.formatting import call_or_format
from sellmo.api.decorators import view, chainable, link
from sellmo.api.exceptions import ViewNotImplemented
from sellmo.api.configuration import define_setting, define_import
from sellmo.api.checkout.models import Order, Shipment, Payment, ORDER_NEW
from sellmo.api.checkout.status import ORDER_STATUSES, OrderStatusesHelper
from sellmo.api.checkout.forms import ShippingMethodForm, PaymentMethodForm
from sellmo.signals.checkout import order_state_changed
    

def method_choice_format(method, costs, **kwargs):
    if costs:
        return u"{method} +{costs}".format(method=method, costs=costs)
    return u"{method}".format(method=method)


class CheckoutModule(sellmo.Module):

    namespace = 'checkout'
    enabled = True

    Order = Order
    Shipment = Shipment
    Payment = Payment
    
    ShippingMethodForm = define_import(
        'SHIPPING_METHOD_FORM',
        default='sellmo.api.checkout.forms.ShippingMethodForm')
        
    shipping_method_choice_format = define_setting(
        'SHIPPING_METHOD_CHOICE_FORMAT',
        default=method_choice_format)
        
    PaymentMethodForm = define_import(
        'PAYMENT_METHOD_FORM',
        default='sellmo.api.checkout.forms.PaymentMethodForm')
        
    payment_method_choice_format = define_setting(
        'PAYMENT_METHOD_CHOICE_FORMAT',
        default=method_choice_format)

    CheckoutProcess = define_import('CHECKOUT_PROCESS')
    
    order_statuses = define_setting(
        'ORDER_STATUSES',
        default=ORDER_STATUSES,
        transform=lambda value : OrderStatusesHelper(value))
    
    def __init__(self, *args, **kwargs):
        # Hookup signals
        order_state_changed.connect(self.on_order_state_changed)

    def on_order_state_changed(self, sender, order, new_state, old_state=None,
                               **kwargs):
        if old_state == ORDER_NEW:
            # Try find cart for this order
            purchases = order.purchases.filter(cart__isnull=False)[:1]
            if purchases:
                cart = purchases[0].cart
                # Cart won't be needed anymore
                cart.delete()

    # FORMS

    @chainable()
    def get_shipping_method_form(self, chain, order, prefix=None, data=None,
                                 form=None, methods=None, method=None, 
                                 **kwargs):
        if methods is None:
            methods = self.get_shipping_methods(order=order)
        if form is None:
            class ShippingMethodForm(self.ShippingMethodForm):
                choices = [
                    (method.identifier,
                     self.get_shipping_method_choice(method=method, 
                                                     order=order))
                    for method in methods.values()
                    if method.is_available(order=order)
                ]
                method = forms.ChoiceField(
                    widget=forms.RadioSelect(),
                    choices=choices,
                    initial=choices[0][0] if choices else None
                )
            initial = {}
            if method:
                initial['method'] = method.identifier
            form = ShippingMethodForm(data, prefix=prefix, initial=initial)
        if chain:
            out = chain.execute(
                order=order, prefix=prefix, data=data, form=form, **kwargs)
            if out.has_key('form'):
                form = out['form']
        return form

    @chainable()
    def get_shipping_method_choice(self, chain, order, method, choice=None,
                                   **kwargs):
        if choice is None:
            costs = method.get_costs(order=order)
            choice = call_or_format(
                self.shipping_method_choice_format,
                method=method,
                costs=costs
            )
        if chain:
            out = chain.execute(
                method=method, order=order, choice=choice, **kwargs)
            if out.has_key('choice'):
                choice = out['choice']
        return choice

    @chainable()
    def get_payment_method_form(self, chain, order, prefix=None, data=None,
                                form=None, methods=None, method=None,
                                **kwargs):
        if methods is None:
            methods = self.get_payment_methods(order=order)
        if form is None:
            class PaymentMethodForm(self.PaymentMethodForm):
                choices = [
                    (method.identifier, self.get_payment_method_choice(
                        method=method, order=order))
                    for method in methods.values()
                    if method.is_available(order=order)
                ]
                method = forms.ChoiceField(
                    widget=forms.RadioSelect(),
                    choices=choices,
                    initial=choices[0][0] if choices else None
                )
            initial = {}
            if method:
                initial['method'] = method.identifier
            form = PaymentMethodForm(data, prefix=prefix, initial=initial)
        if chain:
            out = chain.execute(
                order=order, prefix=prefix, data=data, form=form, **kwargs)
            if out.has_key('form'):
                form = out['form']
        return form

    @chainable()
    def get_payment_method_choice(self, chain, order, method, choice=None,
                                  **kwargs):
        if choice is None:
            costs = method.get_costs(order=order)
            choice = call_or_format(
                self.payment_method_choice_format,
                method=method,
                costs=costs
            )
        if chain:
            out = chain.execute(
                method=method, order=order, choice=choice, **kwargs)
            if out.has_key('choice'):
                choice = out['choice']
        return choice

    @view([r'^step/(?P<step>[-a-zA-Z0-9_]+)/$', r'^$'])
    def checkout(self, chain, request, step=None, data=None, order=None,
                 process=None, context=None, **kwargs):

        if context is None:
            context = {}

        # Try resolve data
        if data is None and request.method == 'POST':
            data = request.POST

        # Retrieve order from request
        if order is None:
            order = self.get_order(request=request)

        # Try initialize order from cart
        if not order and modules.cart.enabled:
            cart = modules.cart.get_cart(request=request)
            self.cart_to_order(cart=cart, order=order)

        # Now make sure this order has some actual purchases
        if not order:
            raise Http404("Nothing to order.")

        if process is None:
            process = self.get_checkout_process(request=request, order=order)

        redirection = None

        # Perform atomic transactions at this point
        with transaction.atomic():
            # Move to the appropiate step
            if step:
                try:
                    # Go to the given step
                    process.step_to(step)
                except ProcessError as error:
                    raise Http404(error)

                # Feed the process
                if data:
                    if process.feed(data):
                        # Try to track the order at this point
                        try:
                            order.track(request)
                        except UntrackableError:
                            pass

                        if not process.completed:
                            redirection = redirect(reverse(
                                'checkout.checkout',
                                kwargs={'step': process.current_step.key}))
            else:
                try:
                    # Go to the latest step
                    process.step_to_latest()
                except ProcessError as error:
                    raise Http404(error)

                redirection = redirect(reverse(
                    'checkout.checkout',
                    kwargs={'step': process.current_step.key}))

        # See if we completed the process
        if process.completed:

            # Untrack the order at this point
            order.untrack(request)

            # Redirect away from this view
            request.session['completed_order'] = order.pk
            redirection = redirect(reverse('checkout.complete'))

        if redirection:
            return redirection

        # Append to context
        context['order'] = order
        context['process'] = process

        if chain:
            return chain.execute(
                request=request, step=step, order=order,
                process=process, context=context, **kwargs)

        try:
            return process.render(request, context=context)
        except ProcessError as error:
            raise Http404(error)

    @view(r'^complete/$')
    def complete(self, chain, request, order=None, context=None, **kwargs):

        if context is None:
            context = {}

        # Retrieve order from session data
        order = self.get_completed_order(request=request)
        if order is None:
            raise Http404("No order has been checked out.")

        # Append to context
        context['order'] = order
        if chain:
            return chain.execute(
                request, order=order, context=context, **kwargs)
        else:
            # We don't render anything
            raise Http404

    @view(r'^cancel/$')
    def cancel(self, chain, request, order=None, data=None, context=None,
               **kwargs):

        if context is None:
            context = {}

        # Try resolve data
        if data is None and request.method == 'POST':
            data = request.POST

        # Retrieve order from request
        if order is None:
            order = self.get_order(request=request)

        #
        if not order:
            raise Http404("No order to cancel.")

        if not order.may_cancel:
            raise Http404("This order may not be cancelled.")

        #
        if data and 'cancel_order' in data:
            order.cancel()
            order.untrack(request)

        # Append to context
        context['order'] = order

        if chain:
            return chain.execute(
                request, order=order, data=data, context=context, **kwargs)
        else:
            raise ViewNotImplemented

    @chainable()
    def get_checkout_process(self, chain, request, order, process=None, **kwargs):
        if process is None:
            process = self.CheckoutProcess(order=order, request=request)
        if chain:
            out = chain.execute(
                process=process, order=order, request=request, **kwargs)
            process = out.get('process', process)
        return process

    # SHIPPING LOGIC

    @chainable()
    def get_shipping_methods(self, chain, order, methods=None, **kwargs):
        if methods is None:
            methods = {}
        if chain:
            out = chain.execute(order=order, methods=methods, **kwargs)
            methods = out.get('methods', methods)
        return methods

    @chainable()
    def process_shipping_method(self, chain, request, order, prefix=None,
                                data=None, method=None, **kwargs):
        methods = self.get_shipping_methods(order=order)
        processed = False
        initial = None

        if order.shipment:
            initial = order.shipment.get_method()

        form = self.get_shipping_method_form(
            order=order, prefix=prefix, data=data, 
            methods=methods, method=initial)

        if data and form.is_valid():
            # Resolve shipping method
            method = form.cleaned_data['method']
            method = methods[method]
            # We need to invalidate the order first, this clears any choosen
            # payment method. Payment method is dependant on shipping method.
            order.invalidate()
            method.ship(order)
            # Re-calculate, use existing subtotal
            order.calculate(subtotal=order.subtotal)
            processed = True

        if chain:
            out = chain.execute(
                request=request,
                order=order,
                prefix=prefix,
                data=data,
                method=method,
                form=form,
                processed=processed,
                **kwargs
            )
            method, form, processed = out.get('method', method), out.get(
                'form', form), out.get('processed', processed)
        return method, form, processed

    # PAYMENT LOGIC

    @chainable()
    def get_payment_methods(self, chain, order, methods=None, **kwargs):
        if methods is None:
            methods = {}
        if chain:
            out = chain.execute(order=order, methods=methods, **kwargs)
            methods = out.get('methods', methods)
        return methods

    @chainable()
    def process_payment_method(self, chain, request, order, prefix=None,
                               data=None, method=None, **kwargs):
        methods = self.get_payment_methods(order=order)
        processed = False
        initial = None

        if order.payment:
            initial = order.payment.get_method()

        form = self.get_payment_method_form(
            order=order, prefix=prefix, data=data,
            methods=methods, method=initial)

        if data and form.is_valid():
            # Resolve payment method
            method = form.cleaned_data['method']
            method = methods[method]
            method.pay(order)
            order.calculate(subtotal=order.subtotal)
            processed = True

        if chain:
            out = chain.execute(
                request=request,
                order=order,
                prefix=prefix,
                data=data,
                method=method,
                form=form,
                processed=processed,
                **kwargs
            )
            method, form, processed = out.get('method', method), out.get(
                'form', form), out.get('processed', processed)
        return method, form, processed

    @chainable()
    def get_order(self, chain, request=None, order=None, **kwargs):
        if order is None:
            order = self.Order.objects.try_get_tracked(request)
            if not order.is_new and not order.is_pending:
                order.untrack(request)
                order = self.Order.objects.try_get_tracked(request)
        if chain:
            out = chain.execute(request=request, order=order, **kwargs)
            order = out.get('order', order)
        return order
        
    @chainable()
    def get_completed_order(self, chain, request=None, order=None, **kwargs):
        if order is None:
            # Retrieve order from session data
            try:
                order = self.Order.objects.get(
                    id=request.session.get('completed_order'))
            except self.Order.DoesNotExist:
                pass
        if chain:
            out = chain.execute(request=request, order=order, **kwargs)
            order = out.get('order', order)
        return order

    @chainable()
    def cart_to_order(self, chain, cart, order):
        if cart:
            if order.pk:
                order.clear()
                for purchase in cart:
                    order.add(purchase, calculate=False)
            else:
                order.proxy(cart)
            order.calculate(subtotal=cart.total, save=not order.pk is None)

    @link(namespace='cart')
    def add_purchase(self, request, purchase, cart, **kwargs):
        order = self.get_order(request=request)
        if order.pk:
            if order.may_change:
                order.add(purchase, calculate=False)
                order.invalidate()
                order.calculate(subtotal=cart.total)
            else:
                order.untrack(request)

    @link(namespace='cart')
    def update_purchase(self, request, purchase, cart, **kwargs):
        order = self.get_order(request=request)
        if order.pk and order.may_change:
            order.update(purchase, calculate=False)
            order.invalidate()
            order.calculate(subtotal=cart.total)

    @link(namespace='cart')
    def remove_purchase(self, request, purchase, cart, **kwargs):
        order = self.get_order(request=request)
        if order.pk and order.may_change:
            if purchase in order:
                order.remove(purchase, calculate=False)
            order.invalidate()
            order.calculate(subtotal=cart.total)
    
    @link(namespace='customer')
    def get_customer(self, request, customer=None, **kwargs):
        if customer is None:
            # Retrieve order from session data
            order = self.get_completed_order(request=request)
            if order is not None:
                customer = modules.customer.Contactable.clone(
                    order, cls=modules.customer.Customer)
                if len(modules.customer.address_types) > 0:
                    address = modules.customer.address_types[0]
                    address = order.get_address(address)
                    customer = modules.customer.Addressee.clone(
                        address, clone=customer)
                for address in modules.customer.address_types:
                    customer.set_address(
                        address, order.get_address(address).clone())
        return {
            'customer': customer
        }
