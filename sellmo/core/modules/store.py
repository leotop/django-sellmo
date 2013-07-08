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

from django.db import models
from django.db.models.query import QuerySet

#

import sellmo
from sellmo import modules
from sellmo.api.decorators import view, chainable
from sellmo.modularization import Module
from sellmo.api.store.models import Purchase


#

class StoreModule(sellmo.Module):

    namespace = 'store'
    Purchase = Purchase

    def __init__(self, *args, **kwargs):
        pass
    
    @chainable()
    def merge_purchase(self, chain, purchase, others, result=None, merged=None, **kwargs):
        
        purchase = purchase.downcast()
        manager = purchase.__class__.objects
        
        # Ensure others is a queryset of the given purchase's queryset type
        others = manager.filter(pk__in=[other.pk for other in others])
        
        # Narrow down
        others = others.mergeable_with(purchase)
        if others:
            merged = manager.filter(pk__in=[other.pk for other in others] + [purchase.pk])
            result = manager.merge(merged)
            if result:
                self.make_purchase(purchase=result)
        
        return (result, merged)
        
            
    @chainable()
    def make_purchase(self, chain, product=None, qty=None, purchase=None, **kwargs):
        
        if purchase is None:
            purchase = self.Purchase()
        
        if not product is None:
            purchase.product = product    
        
        if not qty is None:
            purchase.qty = qty
        
        # Always (re) assign price
        purchase.price = purchase.product.get_price(qty=purchase.qty)
            
        if chain:
            out = chain.execute(product=purchase.product, qty=purchase.qty, purchase=purchase, **kwargs)
            if out.has_key('purchase'):
                purchase = out['purchase']
        
        return purchase