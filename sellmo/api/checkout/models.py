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
        
@load(before='finalize_checkout_Order')
def load_model():
    modules.checkout.Order = modules.pricing.make_stampable(
        cls=modules.checkout.Order,
        properties=[
            ('subtotal', _("subtotal")),
            ('total', _("total")),
        ]
    )
        
    class Order(modules.checkout.Order):
        paid = modules.pricing.construct_pricing_field(
            verbose_name = _("paid")
        )
        
        class Meta:
            abstract = True
    modules.checkout.Order = Order
    
@load(before='finalize_checkout_Payment')
def load_model():
    modules.checkout.Payment = modules.pricing.make_stampable(
        cls=modules.checkout.Payment,
        properties=[
            ('costs', _("costs"))
        ]
    )
    
@load(before='finalize_checkout_Shipment')
def load_model():
    modules.checkout.Shipment = modules.pricing.make_stampable(
        cls=modules.checkout.Shipment,
        properties=[
            ('costs', _("costs"))
        ]
    )
    
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
            related_name = 'purchases',
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
    
    _proxy = None
    
    #
    
    objects = TrackingManager('sellmo_order')
    
    #
    
    created = models.DateTimeField(
        auto_now_add = True,
        editable = False,
        verbose_name = _("created at"),
    )
    
    modified = models.DateTimeField(
        auto_now = True,
        editable = False,
        verbose_name = _("modified at"),
    )
    
    status = models.PositiveIntegerField(
        null = True,
        blank = True,
        verbose_name = _("status"),
    )
    
    """
    An accepted order has been successfully checked out.
    """
    accepted = models.BooleanField(
        default = False,
        verbose_name = _("accepted"),
    )
    
    """
    A placed order can no longer be modified by the customer.
    """
    placed = models.BooleanField(
        default = False,
        editable = False,
        verbose_name = _("placed"),
    )
    
    """
    A cancelled order was cancelled by the customer and will not be shown to the customer anymore.
    """
    cancelled = models.BooleanField(
        default = False,
        editable = False,
        verbose_name = _("cancelled"),
    )
    
    """
    Timestamp when this order was last calculated.
    """
    calculated = models.DateTimeField(
        editable = False,
        null = True,
        verbose_name = _("calculated at"),
    )
    
    #
    
    def get_address(self, type):
        try:
            return getattr(self, '{0}_address'.format(type))
        except modules.customer.Address.DoesNotExist:
            return None
        
    def set_address(self, type, value):
        self._not_placed()
        setattr(self, '{0}_address'.format(type), value)
    
    #
    
    def proxy(self, purchases):
        self._proxy = purchases
        
    #
    
    def add(self, purchase, save=True, calculate=True):
        self._not_placed()
        if self.pk == None:
            self.save()
        purchase.order = self
        if save:
            purchase.save()
            if calculate:
                self.calculate()
        
    def update(self, purchase, save=True, calculate=True):
        self._not_placed()
        if purchase.order != self:
            raise Exception("We don't own this purchase")
        if purchase.qty == 0:
            self.remove(purchase, save=False)
        if save:
            purchase.save()
            if calculate:
                self.calculate()
        
    def remove(self, purchase, save=True, calculate=True):
        self._not_placed()
        if purchase.order != self:
            raise Exception("We don't own this purchase")
        purchase.order = None
        if save:
            purchase.save()
            if calculate:
                self.calculate()
        
    def clear(self, save=True, calculate=True):
        self._not_placed()
        for purchase in self:
            self.remove(purchase, save=save, calculate=False)
        if save:
            if calculate:
                self.calculate()
    
    def calculate(self, subtotal=None, total=None, save=True):
        if subtotal is None:
            subtotal = Price()
            for purchase in self:
                subtotal += purchase.total
            subotal = modules.pricing.get_price(price=subtotal, order=self, subtotal=True)
        
        self.subtotal = subtotal
        
        if total is None:
            total = Price()
            total += self.subtotal
            if self.shipment:
                total += self.shipment.costs
            if self.payment:
                total += self.payment.costs
            total = modules.pricing.get_price(price=total, order=self, total=True)
        
        self.total = total
        
        # Update calculcated timestamp and save
        self.calculated = datetime.datetime.now()
        if save:
            self.save()
        
    def place(self):
        self._not_placed()
        if self.calculated is None:
            raise Exception("This order hasn't been calculated.")
        self.placed = True
        self.save()
        
    def accept(self):
        if self.accepted:
            raise Exception("This order has already been accepted.")
        self.accepted = True
        self.save()
        
    def cancel(self): 
        self.cancelled = True
        self.save()
            
    def invalidate(self, force=False, save=True):
        if not force:
            self._not_placed()
        else:
            self.placed = False
        
        self.total = Price()
        self.calculated = None
        self.status = None
        if save:
            self.save()
        
        if self.shipment:
            self.shipment.delete()
        if self.payment:
            self.payment.delete()
            
    @property
    def may_cancel(self):
        return self.placed and not self.accepted
            
    @property
    def may_change(self): 
        return not self.placed and not self.accepted
        
    @property
    def is_paid(self):
        return self.placed and self.total.amount == self.paid
        
    def _not_placed(self):
        if self.placed:
            raise Exception("This order is already placed.")
        
    def __contains__(self, purchase):
        return purchase.order == self
    
    def __iter__(self):
        purchases = self._proxy if self._proxy else []
        if not purchases and hasattr(self, 'purchases'):
            purchases = self.purchases.polymorphic().all()
        
        for purchase in purchases:
            yield purchase
                
    def __len__(self):
        purchases = self._proxy if self._proxy else []
        if not purchases and hasattr(self, 'purchases'):
            return self.purchases.count()
        return len(purchases)
                
    def __nonzero__(self):
        return len(self) > 0
        
    def __unicode__(self):
        return _("order #{0}").format(unicode(self.pk))
    
    class Meta:
        abstract = True
        
class Shipment(PolymorphicModel):
    
    identifier = models.CharField(
        max_length = 80,
    )
    
    def get_method(self):
        return modules.checkout.get_shipping_methods(order=self.order)[self.identifier]
    method = property(get_method)
    
    def __unicode__(self):
        return unicode(self.order)
    
    class Meta:
        abstract = True
        
class Payment(PolymorphicModel):

    identifier = models.CharField(
        max_length = 80,
    )
    
    def __unicode__(self):
        return unicode(self.order)
    
    def get_method(self):
        return modules.checkout.get_payment_methods(order=self.order)[self.identifier]
    method = property(get_method)

    class Meta:
        abstract = True