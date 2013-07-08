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
from django.db.models import Q
from django.db.models.query import QuerySet

#

from sellmo import modules
from sellmo.api.decorators import load
from sellmo.utils.polymorphism import PolymorphicModel, PolymorphicManager, PolymorphicQuerySet

#

@load(after='finalize_product_Product', before='finalize_store_Purchase')
def load_model():
    class Purchase(modules.store.Purchase):
        product = models.ForeignKey(
            modules.product.Product
        )
        class Meta:
            abstract = True
    
    modules.store.Purchase = Purchase
        
@load(action='finalize_store_Purchase', after='finalize_pricing_Stampable')
def finalize_model():
    class Purchase(modules.store.Purchase, modules.pricing.Stampable):
        pass
    modules.store.Purchase = Purchase
    
class PurchaseQuerySet(PolymorphicQuerySet):
    def mergeable_with(self, purchase):
        return self.filter(~Q(pk=purchase.pk), content_type=purchase.content_type, product=purchase.product)

class PurchaseManager(PolymorphicManager):
    def get_query_set(self):
        return PurchaseQuerySet(self.model)

    def mergeable_with(self, *args, **kwargs):
        return self.get_query_set().mergeable_with(*args, **kwargs)
    
    def merge(self, purchases):
        purchase = purchases[0]
        result = modules.store.Purchase(product=purchase.product, qty=0)
        for purchase in purchases:
            result.qty += purchase.qty
        return result

class Purchase(PolymorphicModel):
    
    objects = PurchaseManager()
    
    qty = models.PositiveIntegerField(
        default = 1
    )
    
    @property
    def description(self):
        return self.describe()
        
    @property
    def total(self):
        return self.price ^ self.qty
    
    def describe(self):
        return unicode(self.product)
        
    def clone(self, cls=None):
        clone = super(Purchase, self).clone(cls=cls)
        clone.product = self.product
        clone.qty = self.qty
        clone.price = self.price
        return clone
    
    def __unicode__(self):
        return u"%s x %s" % (self.qty, self.description)
    
    class Meta:
        app_label = 'store'
        abstract = True