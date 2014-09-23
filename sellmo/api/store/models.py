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


import datetime

from django.db import models
from django.db.models import Q
from django.db.models.query import QuerySet
from django.utils.translation import ugettext_lazy as _

from sellmo import modules
from sellmo.api.decorators import load
from sellmo.api.pricing import Price
from sellmo.utils.cloning import Cloneable
from sellmo.core.polymorphism import (PolymorphicModel, PolymorphicManager,
                                      PolymorphicQuerySet)


@load(action='finalize_store_Purchase')
def finalize_model():

    modules.store.Purchase = modules.pricing.make_stampable(
        model=modules.store.Purchase,
        properties=[
            ('subtotal', _("subtotal")),
            ('total', _("total"))
        ]
    )

    class Purchase(modules.store.Purchase):

        class Meta(modules.store.Purchase.Meta):
            app_label = 'store'

    modules.store.Purchase = Purchase


class PurchaseQuerySet(PolymorphicQuerySet):

    def mergeable_with(self, purchase):
        return self.get(~Q(pk=purchase.pk),
                        content_type=purchase.resolve_content_type(),
                        product=purchase.product)


class PurchaseManager(PolymorphicManager):

    def get_queryset(self):
        return PurchaseQuerySet(self.model, using=self._db)

    def mergeable_with(self, *args, **kwargs):
        return self.get_queryset().mergeable_with(*args, **kwargs)


class Purchase(PolymorphicModel, Cloneable):

    objects = PurchaseManager()

    """
    Timestamp when this purchase was last calculated.
    """
    calculated = models.DateTimeField(
        editable=False,
        null=True,
        verbose_name=_("calculated at"),
    )
    
    description = models.CharField(
        max_length=255,
        verbose_name=_("description"),
    )

    qty = models.PositiveIntegerField(
        default=1,
        verbose_name=_("qty"),
    )
    
    product = models.ForeignKey(
        'product.Product',
        verbose_name=_("product"),
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )
    
    def get_subtotal_kwargs(self):
        return {}
        
    def get_total_kwargs(self):
        return {}

    def calculate(self, subtotal=None, total=None, save=True):
        if total is None:
            if subtotal is None:
                subtotal = self.qty * modules.pricing.get_price(
                    product=self.product, qty=self.qty,
                    **self.get_subtotal_kwargs())
            total = modules.pricing.get_price(
                price=subtotal, purchase=self,
                **self.get_total_kwargs())
            
        if subtotal is None:
            subtotal = total
        
        self.subtotal = subtotal
        self.total = total

        # Update calculcated timestamp and save
        self.calculated = datetime.datetime.now()
        if save:
            self.save()

    def merge_with(self, purchase):
        self.qty += purchase.qty
        self.subtotal = Price()
        self.total = Price()
        self.calculated = None

    @property
    def qty_price(self):
        return self.total / self.qty

    def clone(self, cls=None, clone=None):
        clone = super(Purchase, self).clone(cls=cls, clone=clone)
        clone.product = self.product
        clone.description = self.description
        clone.qty = self.qty
        clone.subtotal = self.subtotal
        clone.total = self.total
        clone.calculated = self.calculated
        return clone

    def is_stale(self, **kwargs):
        return True

    def __unicode__(self):
        return self.description

    class Meta:
        abstract = True
        verbose_name = _("purchase")
        verbose_name_plural = ("purchases")
        ordering = ['pk']
        
