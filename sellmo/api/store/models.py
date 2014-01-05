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

import datetime

#

from django.db import models
from django.db.models import Q
from django.db.models.query import QuerySet
from django.utils.translation import ugettext_lazy as _

#

from sellmo import modules
from sellmo.api.decorators import load
from sellmo.api.pricing import Price
from sellmo.utils.polymorphism import PolymorphicModel, PolymorphicManager, PolymorphicQuerySet

#

@load(after='finalize_product_Product', before='finalize_store_Purchase')
def load_model():
    class Purchase(modules.store.Purchase):
        product = models.ForeignKey(
            modules.product.Product,
            verbose_name = _("product"),
        )
        class Meta:
            abstract = True
    
    modules.store.Purchase = Purchase
        
@load(action='finalize_store_Purchase')
def finalize_model():
    
    modules.store.Purchase = modules.pricing.make_stampable(
        cls = modules.store.Purchase,
        properties = [
            ('total', _("total"))
        ]
    )
    
    class Purchase(modules.store.Purchase):
        class Meta:
            app_label = 'store'
            verbose_name = _("purchase")
            verbose_name_plural = ("purchases")
    modules.store.Purchase = Purchase
    
class PurchaseQuerySet(PolymorphicQuerySet):
    def mergeable_with(self, purchase):
        return self.get(~Q(pk=purchase.pk), content_type=purchase.resolve_content_type(), product=purchase.product)

class PurchaseManager(PolymorphicManager):
    def get_query_set(self):
        return PurchaseQuerySet(self.model)

    def mergeable_with(self, *args, **kwargs):
        return self.get_query_set().mergeable_with(*args, **kwargs)

class Purchase(PolymorphicModel):
    
    objects = PurchaseManager()
    
    """
    Timestamp when this purchase was last calculated.
    """
    calculated = models.DateTimeField(
        editable = False,
        null = True,
        verbose_name = _("calculated at"),
    )
    
    qty = models.PositiveIntegerField(
        default = 1,
        verbose_name = _("qty"),
    )
    
    def calculate(self, total=None, save=True):
        if total is None:
            total = self.product.get_price(qty=self.qty) * self.qty
            total = modules.pricing.get_price(price=total, purhase=self)
            
        self.total = total
        
        # Update calculcated timestamp and save
        self.calculated = datetime.datetime.now()
        if save:
            self.save()
    
    def merge_with(self, purchase):
        self.qty += purchase.qty
        self.total = Price()
        self.calculated = None
    
    @property
    def qty_price(self):
        return self.total / self.qty
    
    @property
    def description(self):
        return self.describe()
    
    def describe(self):
        return unicode(self.product)
        
    def clone(self, cls=None, clone=None):
        clone = super(Purchase, self).clone(cls=cls, clone=clone)
        clone.product = self.product
        clone.qty = self.qty
        clone.total = self.total
        clone.calculated = self.calculated
        return clone
    
    def __unicode__(self):
        return u"%s x %s" % (self.qty, self.description)
    
    class Meta:
        abstract = True