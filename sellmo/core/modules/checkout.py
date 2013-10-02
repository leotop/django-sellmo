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


from django.http import Http404
from django.core.urlresolvers import reverse
from django.shortcuts import redirect
from django.db import models
from django import dispatch

#

import sellmo
from sellmo import modules
from sellmo.core.processing import ProcessError
from sellmo.utils.tracking import UntrackableError
from sellmo.api.decorators import view, chainable
from sellmo.api.checkout.models import Order
from sellmo.api.checkout.processes import CheckoutProcess

#

class CheckoutModule(sellmo.Module):

    namespace = 'checkout'
    prefix = 'checkout'
    enabled = True
    Order = Order
    CheckoutProcess = CheckoutProcess
    
    collect_shipping_methods = dispatch.Signal(providing_args=['methods'])
    collect_payment_methods = dispatch.Signal(providing_args=['methods'])
    
    required_address_types = ['shipping', 'billing']
    customer_required = False
    
    def __init__(self, *args, **kwargs):
        pass
        
    @view([r'^(?P<step>[a-z0-9_-]+)/$', r'^$'])
    def checkout(self, chain, request, step=None, data=None, order=None, process=None, context=None, **kwargs):
        
        if context is None:
            context = {}
            
        # Try resolve data
        if data is None and request.method == 'POST':
            data = request.POST
        
        if order is None:
            order = self.get_order(request=request)
        
        if process is None:
            process = self.get_process(request=request, order=order)
        
        # Move to the appropiate step
        if step:
            try:
                process.step_to(step)
            except ProcessError:
                raise Http404
        else:
            try:
                process.step_to_latest()
            except ProcessError:
                raise Http404
            else:
                return redirect(reverse('checkout.checkout', kwargs = {'step' : process.current_step.key})) 
                
        # Feed the process
        if data:
            if process.feed(data):
                # see if we completed the process
                if process.completed:
                    return redirect(reverse('checkout.checkout_complete'))
                else:
                    # Succesfully fed data, redirect to next step
                    return redirect(reverse('checkout.checkout', kwargs = {'step' : process.current_step.key})) 
                
        # Try to track the order
        try:
            order.track(request)
        except UntrackableError:
            pass
                
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
    def get_process(self, chain, request, order=None, process=None, **kwargs):
        if order is None:
            order = self.get_order(request=requst)
        if process is None:
            process = self.CheckoutProcess(order=order, request=request)    
        if chain:
            out = chain.execute(process=process, order=order, request=request, **kwargs)
            if out.has_key('process'):
                process = out['process']
        return process
        
    @chainable()
    def get_order(self, chain, request=None, order=None, **kwargs):
        if order is None:
            order = self.Order.objects.from_request(request)
        if chain:
            out = chain.execute(order=order, request=request, **kwargs)
            if out.has_key('order'):
                order = out['order']
        return order
        
    @chainable()
    def place_order(self, chain, cart=None, **kwargs):
        """
        Places the order and destroys the cart.
        """
        pass
        
    @chainable()
    def get_shipping_method_form(self, chain, prefix=None, data=None, methods=None, form=None, **kwargs):
        if methods is None:
            methods = []
            self.collect_shipping_methods.send(sender=self, methods=methods)
        if form is None:
            form = self.ShippingMethodForm(data, prefix=prefix, methods=methods)
        if chain:
            return chain.execute(prefix=prefix, data=data, methods=methods, form=form, **kwargs)
        return form