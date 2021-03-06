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

from django.http import Http404


from sellmo import modules
from sellmo.api.checkout.models import ORDER_NEW
from sellmo.api.decorators import view, chainable, link
from sellmo.api.exceptions import ViewNotImplemented
from sellmo.api.configuration import define_import


class AccountModule(modules.account):
    
    @view(r'^profile/$')
    def profile(self, chain, request, customer=None, orders=None,
                context=None, **kwargs):
        if context is None:
            context = {}
        
        if customer is None:
            customer = modules.customer.get_customer(request=request)
            
        if customer is None:
            raise Http404("Not a customer.")
            
        if orders is None:
            orders = customer.orders.exclude(state=ORDER_NEW)
            
        context['customer'] = customer
        context['orders'] = orders
        
        if chain:
            return chain.execute(request=request, customer=customer, 
                                 orders=orders, context=context, **kwargs)
        raise ViewNotImplemented
        
    @view(r'^order/(?P<order_number>[-a-zA-Z0-9_]+)/$')
    def order(self, chain, request, order_number, customer=None, order=None,
              context=None, **kwargs):
        
        if context is None:
            context = {}
        
        if customer is None:
            customer = modules.customer.get_customer(request=request)
            
        if customer is None:
            raise Http404("Not a customer.")
            
        if order is None:
            try:
                order = customer.orders.exclude(state=ORDER_NEW) \
                                .get(number=order_number)
            except modules.checkout.Order.DoesNotExist:
                raise Http404("No matching order.")
        
        context['customer'] = customer
        context['order'] = order
        
        if chain:
            return chain.execute(request=request, customer=customer, 
                                 order_number=order_number, order=order,
                                 context=context, **kwargs)
        raise ViewNotImplemented
        