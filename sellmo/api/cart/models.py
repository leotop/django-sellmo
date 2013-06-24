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
from django.utils.translation import ugettext_lazy as _

#

from sellmo import modules
from sellmo.api.decorators import load
from sellmo.api.pricing import Price
from sellmo.utils.sessions import TrackingManager

#

@load(after='finalize_cart_Cart', before='finalize_cart_CartItem')
def load_model():
    class CartItem(modules.cart.CartItem):
        cart = models.ForeignKey(
            modules.cart.Cart,
            related_name = 'items'
        )
        
        class Meta:
            abstract = True
        
    modules.cart.CartItem = CartItem
        
@load(after='finalize_store_Purchase', before='finalize_cart_CartItem')
def load_model():
    class CartItem(modules.cart.CartItem):
        purchase = models.OneToOneField(
            modules.store.Purchase,
            editable = False
        )
        
        class Meta:
            abstract = True
        
    modules.cart.CartItem = CartItem
        
@load(action='finalize_cart_Cart')
def finalize_model():
    class Cart(modules.cart.Cart):
        class Meta:
            verbose_name = _("cart")
            verbose_name_plural = _("carts")
    modules.cart.Cart = Cart
    
@load(action='finalize_cart_CartItem')
def finalize_model():
    class CartItem(modules.cart.CartItem):
        class Meta:
            verbose_name = _("cart item")
            verbose_name_plural = _("cart items")
    modules.cart.CartItem = CartItem

class Cart(models.Model):
    
    objects = TrackingManager('sellmo_cart')
    
    #
    
    created = models.DateTimeField(
        auto_now_add = True,
        editable = False
    )
    
    modified = models.DateTimeField(
        auto_now = True,
        editable = False
    )
    
    #
        
    def add(self, purchase):
        if self.pk == None:
            self.save()
        item = modules.cart.CartItem(cart=self, purchase=purchase)
        item.save()
        
    def remove(self, purchase):
        pass
        
    def clear(self):
        pass
    
    def __iter__(self):
        if hasattr(self, 'items'):
            for item in self.items.all():
                yield item
            
    # Pricing
    @property
    def total(self):
        price = Price()
        for item in self:
            price += item.total
        return price
        
    #
    
    def __unicode__(self):
        return unicode(self.modified)
    
    class Meta:
        app_label = 'cart'
        abstract = True
        
class CartItem(models.Model):
    
    __purchase = None
    @property
    def _purchase(self):
        if self.__purchase is None:
            self.__purchase = self.purchase.downcast()
        return self.__purchase
        
    @property
    def qty(self):
        return self._purchase.qty
        
    @property
    def description(self):
        return self._purchase.description
        
    @property
    def product(self):
        return self._purchase.product
    
    @property
    def total(self):
        return self._purchase.price
    
    def __unicode__(self):
        return unicode(self._purchase)
    
    class Meta:
        app_label = 'cart'
        abstract = True