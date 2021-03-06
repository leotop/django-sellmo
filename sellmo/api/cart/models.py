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


from django import dispatch
from django.db import models
from django.utils import timezone
from django.utils.translation import ugettext_lazy as _

from sellmo import modules
from sellmo.api.decorators import load
from sellmo.api.pricing import Price
from sellmo.utils.tracking import trackable


@load(before='finalize_store_Purchase')
def load_model():
    class Purchase(modules.store.Purchase):
        cart = models.ForeignKey(
            'cart.Cart',
            null=True,
            editable=False,
            on_delete=models.SET_NULL,
            related_name='purchases',
        )

        def is_stale(self, ignore_cart=False, **kwargs):
            return (super(Purchase, self).is_stale(**kwargs)
                    and (self.cart is None or ignore_cart))

        class Meta(modules.store.Purchase.Meta):
            abstract = True

    modules.store.Purchase = Purchase


@load(action='finalize_cart_Cart')
def finalize_model():

    modules.cart.Cart = modules.pricing.make_stampable(
        model=modules.cart.Cart,
        properties=[
            ('subtotal', _("subtotal")),
            ('total', _("total")),
        ]
    )

    class Cart(modules.cart.Cart):

        class Meta(modules.cart.Cart.Meta):
            app_label = 'cart'

    modules.cart.Cart = Cart


class Cart(trackable('sellmo_cart')):

    created = models.DateTimeField(
        auto_now_add=True,
        editable=False,
        verbose_name=_("created at"),
    )

    modified = models.DateTimeField(
        auto_now=True,
        editable=False,
        verbose_name=_("modified at"),
    )
    
    """
    Timestamp when this cart was last calculated.
    """
    calculated = models.DateTimeField(
        editable=False,
        null=True,
        verbose_name=_("calculated at"),
    )

    def add(self, purchase, save=True, calculate=True):
        # Clear cache ! IMPORTANT
        self.__purchases = None
        
        if self.pk is None:
            self.save()
        purchase.cart = self
        
        if save:
            purchase.save()
            if calculate:
                self.calculate()

    def update(self, purchase, save=True, calculate=True):
        # Clear cache ! IMPORTANT
        self.__purchases = None
        
        if purchase.cart != self:
            raise Exception("We don't own this purchase")
            
        if purchase.qty == 0:
            self.remove(purchase, save=False)
        
        if save:
            purchase.save()
            if calculate:
                self.calculate()

    def remove(self, purchase, save=True, calculate=True):
        # Clear cache ! IMPORTANT
        self.__purchases = None
        
        if purchase.cart != self:
            raise Exception("We don't own this purchase")
        
        purchase.cart = None
        
        if save:
            purchase.save()
            if calculate:
                self.calculate()

    def clear(self, save=True, calculate=True):
        # Clear cache ! IMPORTANT
        self.__purchases = None
        
        for purchase in self:
            self.remove(purchase, save=save, calculate=False)
        
        if save:
            if calculate:
                self.calculate()

    def calculate(self, subtotal=None, total=None, save=True):
        if total is None:
            if subtotal is None:
                subtotal = Price()
                for purchase in self:
                    if not purchase.calculated:
                        # Sanity check
                        raise Exception(
                            "Cannot calculate cart, "
                            "purchase was not calculated.")
                    subtotal += purchase.total
            total = modules.pricing.get_price(price=subtotal, cart=self)

        if subtotal is None:
            subtotal = total
            
        self.subtotal = subtotal
        self.total = total

        # Update calculcated timestamp and save
        self.calculated = timezone.now()
        if save:
            self.save()
    
    
    # Cache purchases queryset since prefetching isn't safe.
    __purchases = None
    @property
    def _purchases(self):
        if self.__purchases is None:
            self.__purchases = self.purchases.polymorphic().all()
        return self.__purchases

    def __contains__(self, purchase):
        return purchase.cart == self
    
    def __iter__(self):
        for purchase in self._purchases:
            yield purchase

    def __len__(self):
        return self._purchases.count()

    def __nonzero__(self):
        return len(self) > 0

    def __unicode__(self):
        return unicode(self.modified)

    class Meta:
        abstract = True
        verbose_name = _("cart")
        verbose_name_plural = _("carts")
        ordering = ['-pk']
