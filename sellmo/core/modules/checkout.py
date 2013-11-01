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

from django import forms
from django.http import Http404
from django.core.urlresolvers import reverse
from django.shortcuts import redirect
from django.utils.decorators import method_decorator
from django.db import models

from django import dispatch

#

import sellmo
from sellmo import modules
from sellmo.core.processing import ProcessError
from sellmo.utils.tracking import UntrackableError
from sellmo.api.decorators import view, chainable, link
from sellmo.api.checkout.models import Order, Shipment, Payment
from sellmo.api.checkout.processes import CheckoutProcess

#

# Need this in order for forms to load
from sellmo.api.checkout.forms import *

class CheckoutModule(sellmo.Module):

    namespace = 'checkout'
    prefix = 'checkout'
    enabled = True
    Order = Order
    Shipment = Shipment
    Payment = Payment
    CheckoutProcess = CheckoutProcess
    
    required_address_types = ['shipping', 'billing']
    customer_required = False
    
    ShippingMethodForm = None
    PaymentMethodForm = None
    
    def __init__(self, *args, **kwargs):
        pass
        
    # FORMS
    
    @chainable()
    def get_shipping_method_form(self, chain, order, prefix=None, data=None, form=None, methods=None, method=None, **kwargs):
        if methods is None:
            methods = self.get_shipping_methods(order=order)
        if form is None:
            class ShippingMethodForm(self.ShippingMethodForm):
                method = forms.ChoiceField(
                    widget = forms.RadioSelect(),
                    choices = [(method.identifier, self.get_shipping_method_choice(method=method, order=order)) for method in methods.values()]
                )
            initial = {}
            if method:
                initial['method'] = method.identifier
            form = ShippingMethodForm(data, prefix=prefix, initial=initial)
        if chain:
            out = chain.execute(order=order, prefix=prefix, data=data, form=form, **kwargs)
            if out.has_key('form'):
                form = out['form']
        return form
        
    @chainable()
    def get_shipping_method_choice(self, chain, order, method, choice=None, **kwargs):
        if choice is None:
            costs = method.get_costs(order=order)
            if costs:
                choice = u"{0} + {1}".format(method, costs)
            else:
                choice = unicode(method)
        if chain:
            out = chain.execute(method=method, order=order, choice=choice, **kwargs)
            if out.has_key('choice'):
                choice = out['choice']
        return choice
        
    @chainable()
    def get_payment_method_form(self, chain, order, prefix=None, data=None, form=None, methods=None, method=None, **kwargs):
        if methods is None:
            methods = self.get_payment_methods(order=order)
        if form is None:
            class PaymentMethodForm(self.PaymentMethodForm):
                method = forms.ChoiceField(
                    widget = forms.RadioSelect(),
                    choices = [(method.identifier, self.get_payment_method_choice(method=method, order=order)) for method in methods.values()]
                )
            initial = {}
            if method:
                initial['method'] = method.identifier
            form = PaymentMethodForm(data, prefix=prefix, initial=initial)
        if chain:
            out = chain.execute(order=order, prefix=prefix, data=data, form=form, **kwargs)
            if out.has_key('form'):
                form = out['form']
        return form
        
    @chainable()
    def get_payment_method_choice(self, chain, order, method, choice=None, **kwargs):
        if choice is None:
            costs = method.get_costs(order=order)
            if costs:
                choice = u"{0} + {1}".format(method, costs)
            else:
                choice = unicode(method)
        if chain:
            out = chain.execute(method=method, order=order, choice=choice, **kwargs)
            if out.has_key('choice'):
                choice = out['choice']
        return choice
    
    @view([r'^(?P<step>[a-z0-9_-]+)/$', r'^$'])
    def checkout(self, chain, request, step=None, data=None, order=None, process=None, context=None, **kwargs):
        
        if context is None:
            context = {}
            
        # Try resolve data
        if data is None and request.method == 'POST':
            data = request.POST
        
        # Retrieve order from request
        if order is None:
            order = self.get_order(request=request)
            
        # If this order is newly created, populate from cart and persist it
        if not order.pk:
            cart = modules.cart.get_cart(request=request)
            for item in cart:
                order.add(item)
            
        # Try to track the order
        try:
            order.track(request)
        except UntrackableError:
            raise Exception("Could not track this order")
            
        # Now make sure this order has some actual purchases
        if not order:
            raise Exception("Nothing to order")
        
        if process is None:
            process = self.get_process(request=request, order=order)
        
        # Move to the appropiate step
        if step:
            try:
                process.step_to(step)
            except ProcessError as error:
                raise Http404(error)
        else:
            try:
                process.step_to_latest()
            except ProcessError as error:
                raise Http404(error)
            else:
                return redirect(reverse('checkout.checkout', kwargs = {'step' : process.current_step.key})) 
                
        # Feed the process
        redirection = None
        if data:
            if process.feed(data):
                # see if we completed the process
                if process.completed:
                    # Now place the order
                    self.place_order(request=request, order=order)
                    
                    # Checkout process completed, redirect
                    redirection = redirect(reverse('checkout.checkout_complete'))
                else:
                    # Succesfully fed data, redirect to next step
                    redirection = redirect(reverse('checkout.checkout', kwargs = {'step' : process.current_step.key})) 
            
        if redirection:
            return redirection
                
        # Append to context
        context['order'] = order
        context['process'] = process
        
        if chain:
            return chain.execute(request, step=step, order=order, process=process, context=context, **kwargs)
        return process.render(request, context=context)
        
    @view(r'^checkout_complete/$')
    def checkout_complete(self, chain, request, **kwargs):        
        if chain:
            return chain.execute(request, **kwargs)
        else:
            # We don't render anything
            raise Http404
        
    @chainable()
    def get_process(self, chain, request, order, process=None, **kwargs):
        if process is None:
            process = self.CheckoutProcess(order=order, request=request)    
        if chain:
            out = chain.execute(process=process, order=order, request=request, **kwargs)
            if out.has_key('process'):
                process = out['process']
        return process
        
    # SHIPPING LOGIC
        
    @chainable()
    def get_shipping_methods(self, chain, order, methods=None, **kwargs):
        if methods is None:
            methods = {}
        if chain:
            out = chain.execute(order=order, methods=methods, **kwargs)
            if out.has_key('methods'):
                methods = out['methods']
        return methods
        
    @chainable()
    def handle_shipping_method(self, chain, order, prefix=None, data=None, method=None, **kwargs):
        methods = self.get_shipping_methods(order=order)
        processed = False
        initial = None
        if order.shipment:
            initial = order.shipment.method
        form = self.get_shipping_method_form(order=order, prefix=prefix, data=data, methods=methods, method=initial)
        if data and form.is_valid():
            # Resolve shipping method
            method = form.cleaned_data['method']
            method = methods[method]
            method.ship(order)
            processed = True
        if chain:
            return chain.execute(order=order, prefix=prefix, data=data, method=method, form=form, processed=processed, **kwargs)
        return method, form, processed
        
    # PAYMENT LOGIC
        
    @chainable()
    def get_payment_methods(self, chain, order, methods=None, **kwargs):
        if methods is None:
            methods = {}
        if chain:
            out = chain.execute(order=order, methods=methods, **kwargs)
            if out.has_key('methods'):
                methods = out['methods']
        return methods
        
    @chainable()
    def handle_payment_method(self, chain, order, prefix=None, data=None, method=None, **kwargs):
        methods = self.get_payment_methods(order=order)
        processed = False
        initial = None
        if order.payment:
            initial = order.payment.method
        form = self.get_payment_method_form(order=order, prefix=prefix, data=data, methods=methods, method=initial)
        if data and form.is_valid():
            # Resolve payment method
            method = form.cleaned_data['method']
            method = methods[method]
            method.pay(order)
            processed = True
        if chain:
            return chain.execute(order=order, prefix=prefix, data=data, method=method, form=form, processed=processed, **kwargs)
        return method, form, processed
        
    @chainable()
    def get_order(self, chain, request=None, order=None, **kwargs):
        if order is None:
            order = self.Order.objects.from_request(request)    
        if chain:
            out = chain.execute(request=request, order=order, **kwargs)
            if out.has_key('order'):
                order = out['order']
        return order
        
    @link(namespace='cart')
    def on_purchase(self, request, cart, purchase):
        order = self.get_order(request=request)
        if order.pk:
            if not purchase in order:
                order.add(purchase)
            else:
                order.update(purchase)
            self.invalidate_order(request=request, order=order)
        
    @link(namespace='cart')
    def on_remove_purchase(self, request, cart, purchase):
        order = self.get_order(request=request)
        if order.pk:
            if purchase in order:
                order.remove(purchase)
            self.invalidate_order(request=request, order=order)
    
    @chainable()
    def calculate_order(self, chain, request, order, **kwargs):
        """
        Calculate's the order purchase(s) price
        """
        order.calculate()
        
    @chainable()
    def invalidate_order(self, chain, request, order, **kwargs):
        """
        Invalidates the order after it's purchases have changed
        """
        order.invalidate()
        
    @chainable()
    def place_order(self, chain, request, order, **kwargs):
        """
        Places the order and destroys the cart.
        """
        if order.placed:
            raise Exception("This order is already placed.")
        order.place()