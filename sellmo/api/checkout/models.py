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


#

import datetime

#

from django.db import models
from django.utils.translation import ugettext_lazy as _

#

from sellmo import modules
from sellmo.api.pricing import Price
from sellmo.api.decorators import load
from sellmo.utils.polymorphism import PolymorphicModel
from sellmo.utils.tracking import TrackingManager

#
        
@load(after='finalize_pricing_Stampable', before='finalize_checkout_Order')
def load_model():
    class Order(modules.checkout.Order, modules.pricing.Stampable):
        class Meta:
            abstract = True
    modules.checkout.Order = Order
    
@load(after='finalize_pricing_Stampable', before='finalize_checkout_Payment')
def load_model():
    class Payment(modules.checkout.Payment, modules.pricing.Stampable):
        class Meta:
            abstract = True
    modules.checkout.Payment = Payment
    
@load(after='finalize_pricing_Stampable', before='finalize_checkout_Shipment')
def load_model():
    class Shipment(modules.checkout.Shipment, modules.pricing.Stampable):
        class Meta:
            abstract = True
    modules.checkout.Shipment = Shipment
    
@load(after='finalize_checkout_Payment', before='finalize_checkout_Order')
@load(after='finalize_checkout_Shipment', before='finalize_checkout_Order')
def load_model():
    class Order(modules.checkout.Order):
        payment = models.OneToOneField(
            modules.checkout.Payment,
            related_name = 'order',
            null = True,
            blank = True,
            on_delete = models.SET_NULL,
            verbose_name = _("payment")
        )
        
        shipment = models.OneToOneField(
            modules.checkout.Shipment,
            related_name = 'order',
            null = True,
            blank = True,
            on_delete = models.SET_NULL,
            verbose_name = _("shipment")
        )
        
        class Meta:
            abstract = True
    modules.checkout.Order = Order
    
@load(after='finalize_customer_Customer', before='finalize_checkout_Order')
@load(after='finalize_customer_Contactable', before='finalize_checkout_Order')
def load_model():
    class Order(modules.checkout.Order):
        
        customer =  models.ForeignKey(
             modules.customer.Customer,
             null = not modules.checkout.customer_required,
             blank = not modules.checkout.customer_required,
             related_name = 'orders',
             verbose_name = _("customer"),
         )
        
        class Meta:
            abstract = True
            
    if not modules.checkout.customer_required:
        class Order(Order, modules.customer.Contactable):
            class Meta:
                abstract = True
    
    modules.checkout.Order = Order
    
@load(after='finalize_customer_Address', before='finalize_checkout_Order')
def load_model():
    for type in modules.checkout.required_address_types:
        name = '{0}_address'.format(type)
        modules.checkout.Order.add_to_class(name,
            models.ForeignKey(
                modules.customer.Address,
                null = True,
                related_name='+',
                verbose_name = _("{0} address".format(type)),
            )
        )
        
@load(after='finalize_checkout_Order', before='finalize_store_Purchase')
def load_model():
    class Purchase(modules.store.Purchase):
        order = models.ForeignKey(
            modules.checkout.Order,
            null = True,
            editable = False,
            on_delete = models.SET_NULL,
            related_name = 'items',
            verbose_name = _("order"),
        )

        class Meta:
            abstract = True

    modules.store.Purchase = Purchase
        
@load(action='finalize_checkout_Order')
def finalize_model():
    class Order(modules.checkout.Order):
        class Meta:
            app_label = 'checkout'
            verbose_name = _("order")
            verbose_name_plural = _("orders")
            
    modules.checkout.Order = Order
    
@load(action='finalize_checkout_Shipment')
def finalize_model():
    class Shipment(modules.checkout.Shipment):
        class Meta:
            app_label = 'checkout'
            verbose_name = _("shipment")
            verbose_name_plural = _("shipments")
    
    modules.checkout.Shipment = Shipment
    
@load(action='finalize_checkout_Payment')
def finalize_model():
    class Payment(modules.checkout.Payment):
        class Meta:
            app_label = 'checkout'
            verbose_name = _("payment")
            verbose_name_plural = _("payments")
            
    modules.checkout.Payment = Payment

class Order(models.Model):
    
    objects = TrackingManager('sellmo_order')
    
    #
    
    created = models.DateTimeField(
        auto_now_add = True,
        editable = False
    )
    
    modified = models.DateTimeField(
        auto_now = True,
        editable = False
    )
    
    placed = models.BooleanField(
        default = False,
        editable = False
    )
    
    calculated = models.DateTimeField(
        editable = False,
        null = True
    )
    
    #
    
    def get_address(self, type):
        return getattr(self, '{0}_address'.format(type))
        
    def set_address(self, type, value):
        setattr(self, '{0}_address'.format(type), value)
    
    #
    
    def add(self, purchase, save=True):
        if self.pk == None:
            self.save()
        purchase.order = self
        if save:
            purchase.save()
        
    def update(self, purchase, save=True):
        if purchase.order != self:
            raise Exception("We don't own this purchase")
        if purchase.qty == 0:
            self.remove(purchase, save=False)
        if save:
            purchase.save()
        
    def remove(self, purchase, save=True):
        if purchase.order != self:
            raise Exception("We don't own this purchase")
        purchase.order = None
        if save:
            purchase.save()
        
    def clear(self):
        for purchase in self:
            self.remove(purchase)
            
    def calculate(self, price=None):
        if price is None:
            price = Price()
            for purchase in self:
                price += purchase.total
            price = modules.pricing.get_price(price=price, order=self)
        self.price = price
        self.calculated = datetime.datetime.now()
        self.save()
            
    def invalidate(self):
        self.price = Price()
        self.calculated = None
        self.save()
        if self.shipment:
            self.shipment.delete()
        if self.payment:
            self.payment.delete()
        
    def place(self):
        if self.placed:
            raise Exception("This order is already placed.")
        if self.calculated is None:
            raise Exception("This order hasn't been calculated.")   
        
        self.placed = True
        self.save()
        
    @property
    def total(self):
        return self.price + self.shipment.price + self.payment.price
        
    def __contains__(self, purchase):
        return purchase.order == self
    
    def __iter__(self):
        if hasattr(self, 'items'):
            for item in self.items.polymorphic().all():
                yield item
                
    def __len__(self):
        return self.items.count()
                
    def __nonzero__(self):
        return self.items.count() > 0
    
    class Meta:
        abstract = True
        
class Shipment(PolymorphicModel):
    
    identifier = models.CharField(
        max_length = 80,
    )
    
    def get_method(self):
        return modules.checkout.get_shipping_methods(order=self.order)[self.identifier]
    method = property(get_method)
    
    class Meta:
        abstract = True
        
class Payment(PolymorphicModel):

    identifier = models.CharField(
        max_length = 80,
    )
    
    def get_method(self):
        return modules.checkout.get_payment_methods(order=self.order)[self.identifier]
    method = property(get_method)

    class Meta:
        abstract = True