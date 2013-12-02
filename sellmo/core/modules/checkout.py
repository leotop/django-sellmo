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
from sellmo.signals.checkout import *
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
    
    @view([r'^step/(?P<step>[a-z0-9_-]+)/$', r'^$'])
    def checkout(self, chain, request, step=None, data=None, order=None, process=None, context=None, **kwargs):
        
        if context is None:
            context = {}
            
        # Try resolve data
        if data is None and request.method == 'POST':
            data = request.POST
        
        # Retrieve order from request
        if order is None:
            order = self.get_order(request=request)
            
        # Now make sure this order can be checed out
        if order.accepted:
            raise Http404("This order has already been accepted")
        
        # Try initialize order from cart
        if not order and modules.cart.enabled:
            cart = modules.cart.get_cart(request=request)
            self.cart_to_order(cart=cart, order=order)
            
        # Now make sure this order has some actual purchases
        if not order:
            raise Http404("Nothing to order")
        
        if process is None:
            process = self.get_process(request=request, order=order)
        
        redirection = None
        
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
                        redirection = redirect(reverse('checkout.checkout', kwargs = {'step' : process.current_step.key}))  
        else:
            try:
                # Go to the latest step
                process.step_to_latest()
            except ProcessError as error:
                raise Http404(error)
                
            redirection = redirect(reverse('checkout.checkout', kwargs = {'step' : process.current_step.key}))  
                
        # See if we completed the process
        if process.completed:
            # Checkout process completed, accept the order
            if not order.accepted:
                self.accept_order(request=request, order=order)
            
            # Redirect away from this view
            request.session['completed_order'] = order.pk
            redirection = redirect(reverse('checkout.complete'))
            
        if redirection:
            return redirection
                
        # Append to context
        context['order'] = order
        context['process'] = process
        
        if chain:
            return chain.execute(request, step=step, order=order, process=process, context=context, **kwargs)
        return process.render(request, context=context)
        
    @view(r'^complete/$')
    def complete(self, chain, request, order=None, context=None, **kwargs):
    
        if context is None:
            context = {}
            
        # Retrieve order from session data
        order = request.session.get('completed_order')
        try:
            order = self.Order.objects.get(id=order)
        except self.Order.DoesNotExist:
            raise Http404("No order has been checked out")
            
        # Append to context
        context['order'] = order
        
        if chain:
            return chain.execute(request, order=order, context=context, **kwargs)
        else:
            # We don't render anything
            raise Http404
            
    @view(r'^cancel/$')
    def cancel(self, chain, request, order=None, data=None, context=None, **kwargs):
    
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
            raise Http404("No order to cancel")
            
        if not order.may_cancel:
            raise Http404("Cannot cancel this order")
            
        #
        if data and 'cancel_order' in data:
            self.cancel_order(request=request, order=order)
            
        # Append to context
        context['order'] = order
        
        if chain:
            return chain.execute(request, order=order, data=data, context=context, **kwargs)
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
            order.calculate(subtotal=order.subtotal)
            processed = True
        if chain:
            out = chain.execute(order=order, prefix=prefix, data=data, method=method, form=form, processed=processed, **kwargs)
            method, form, processed = out.get('method', method), out.get('form', form), out.get('processed', processed)
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
            order.calculate(subtotal=order.subtotal)
            processed = True
        if chain:
            out = chain.execute(order=order, prefix=prefix, data=data, method=method, form=form, processed=processed, **kwargs)
            method, form, processed = out.get('method', method), out.get('form', form), out.get('processed', processed)
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
    def add_purchase(self, request, cart, purchase, **kwargs):
        order = self.get_order(request=request)
        if order.pk and order.may_change:
            order.add(purchase, calculate=False)
            order.calculate(subtotal=cart.total)
            self.invalidate_order(request=request, order=order)
            
    @link(namespace='cart')
    def update_purchase(self, request, cart, purchase, **kwargs):
        order = self.get_order(request=request)
        if order.pk and order.may_change:
            order.update(purchase, calculate=False)
            order.calculate(subtotal=cart.total)
            self.invalidate_order(request=request, order=order)
        
    @link(namespace='cart')
    def remove_purchase(self, request, cart, purchase, **kwargs):
        order = self.get_order(request=request)
        if order.pk and order.may_change:
            if purchase in order:
                order.remove(purchase, calculate=False)
            
            order.calculate(subtotal=cart.total)
            self.invalidate_order(request=request, order=order)
        
    @chainable()
    def invalidate_order(self, chain, request, order, **kwargs):
        """
        Invalidates the order after it's purchases have changed.
        """
        order.invalidate()
        if chain:
            chain.execute(request=request, order=order, **kwargs)
    
    @chainable()
    def accept_order(self, chain, request, order, **kwargs):
        """
        Accepts the order and untracks it.
        """
        order.accept()
        order.untrack(request)
        if chain:
            chain.execute(request=request, order=order, **kwargs)
        
        order_accepted.send(sender=self, order=order)
        
    @chainable()
    def place_order(self, chain, request, order, **kwargs):
        """
        Places the order.
        """
        order.place()
        if chain:
            chain.execute(request=request, order=order, **kwargs)
        
        order_placed.send(sender=self, order=order)
            
    @chainable()
    def cancel_order(self, chain, request, order, **kwargs):
        """
        Cancels the order.
        """
        order.cancel()
        order.untrack(request)
        if chain:
            chain.execute(request=request, order=order, **kwargs)
        
        order_cancelled.send(sender=self, order=order)
            
    @link(namespace='customer')
    def get_customer(self, request, customer=None, **kwargs):
        if customer is None:
            # Retrieve order from session data
            order = request.session.get('completed_order')
            try:
                order = self.Order.objects.get(id=order)
            except self.Order.DoesNotExist:
                pass
            else:
                customer = modules.customer.Contactable.clone(order, cls=modules.customer.Customer)
                if len(modules.customer.address_types) > 0:
                    address = modules.customer.address_types[0]
                    address = order.get_address(address)
                    customer = modules.customer.Addressee.clone(address, clone=customer)
                for address in modules.customer.address_types:
                    customer.set_address(address, order.get_address(address).clone())
        return {
            'customer' : customer
        }
        