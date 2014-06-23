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
from django.core.exceptions import ValidationError
from django.utils.translation import ugettext_lazy as _

from sellmo import modules
from sellmo.api.pricing import Price
from sellmo.api.decorators import load
from sellmo.core.polymorphism import (PolymorphicModel,
                                      PolymorphicManager,
                                      PolymorphicOneToOneField)
from sellmo.utils.tracking import trackable
from sellmo.signals.checkout import *


ORDER_NEW = 'new'
ORDER_PENDING = 'pending'
ORDER_COMPLETED = 'completed'
ORDER_CLOSED = 'closed'
ORDER_CANCELED = 'canceled'


@load(before='finalize_checkout_Order')
def load_model():
    modules.checkout.Order = modules.pricing.make_stampable(
        model=modules.checkout.Order,
        properties=[
            ('subtotal', _("subtotal")),
            ('total', _("total")),
        ]
    )

    class Order(modules.checkout.Order):
        paid = modules.pricing.construct_pricing_field(
            verbose_name=_("paid")
        )

        class Meta(modules.checkout.Order.Meta):
            abstract = True

    modules.checkout.Order = Order


@load(before='finalize_checkout_Payment')
def load_model():
    modules.checkout.Payment = modules.pricing.make_stampable(
        model=modules.checkout.Payment,
        properties=[
            ('costs', _("costs"))
        ]
    )


@load(before='finalize_checkout_Shipment')
def load_model():
    modules.checkout.Shipment = modules.pricing.make_stampable(
        model=modules.checkout.Shipment,
        properties=[
            ('costs', _("costs"))
        ]
    )


@load(after='finalize_customer_Contactable')
@load(before='finalize_checkout_Order')
def load_model():
    
    statuses = modules.checkout.order_statuses
    
    class Order(modules.checkout.Order):

        customer = models.ForeignKey(
            'customer.Customer',
            null=not modules.customer.customer_required,
            blank=not modules.customer.customer_required,
            related_name='orders',
            verbose_name=_("customer"),
        )

        status = models.CharField(
            max_length=40,
            default=statuses.initial,
            choices=statuses.choices,
            blank=False,
            verbose_name=_("status"),
        )

        class Meta(modules.checkout.Order.Meta):
            abstract = True

    modules.checkout.Order = Order

    if not modules.customer.customer_required:
        class Order(modules.checkout.Order, modules.customer.Contactable):
            class Meta(
                    modules.checkout.Order.Meta,
                    modules.customer.Contactable.Meta):
                abstract = True

        modules.checkout.Order = Order


@load(before='finalize_checkout_Order')
def load_model():

    for type in modules.customer.address_types:
        name = '{0}_address'.format(type)
        modules.checkout.Order.add_to_class(
            name,
            models.OneToOneField(
                'customer.Address',
                null=True,
                related_name='+',
                verbose_name=_(
                    "{0} address".format(type)),
            )
        )


@load(before='finalize_store_Purchase')
def load_model():
    class Purchase(modules.store.Purchase):
        order = models.ForeignKey(
            'checkout.Order',
            null=True,
            editable=False,
            related_name='purchases',
            verbose_name=_("order"),
        )

        def is_stale(self, ignore_order=False, **kwargs):
            return (super(Purchase, self).is_stale(**kwargs)
                    and (self.order is None or ignore_order))

        class Meta(modules.store.Purchase.Meta):
            abstract = True

    modules.store.Purchase = Purchase


@load(action='finalize_checkout_Order')
def finalize_model():
    class Order(modules.checkout.Order):

        class Meta(modules.checkout.Order.Meta):
            app_label = 'checkout'

    modules.checkout.Order = Order


@load(action='finalize_checkout_Shipment')
def finalize_model():
    class Shipment(modules.checkout.Shipment):

        class Meta(modules.checkout.Shipment.Meta):
            app_label = 'checkout'

    modules.checkout.Shipment = Shipment


@load(action='finalize_checkout_Payment')
def finalize_model():
    class Payment(modules.checkout.Payment):

        class Meta(modules.checkout.Payment.Meta):
            app_label = 'checkout'

    modules.checkout.Payment = Payment


class Order(trackable('sellmo_order')):

    _proxy = None
    
    @staticmethod
    def generate_order_number(order):
        return unicode(order.pk)

    number = models.CharField(
        max_length=80,
        blank=True,
        verbose_name=_("order number"),
    )
    
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

    state = models.CharField(
        max_length=20,
        editable=False,
        default=ORDER_NEW,
    )

    """
    Timestamp when this order was last calculated.
    """
    calculated = models.DateTimeField(
        editable=False,
        null=True,
        verbose_name=_("calculated at"),
    )
    
    payment = PolymorphicOneToOneField(
        'checkout.Payment',
        related_name='order',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        verbose_name=_("payment")
    )
    
    shipment = PolymorphicOneToOneField(
        'checkout.Shipment',
        related_name='order',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        verbose_name=_("shipment")
    )

    def get_address(self, type):
        try:
            return getattr(self, '{0}_address'.format(type))
        except modules.customer.Address.DoesNotExist:
            return None

    def set_address(self, type, value):
        self.ensure_state(ORDER_NEW)
        setattr(self, '{0}_address'.format(type), value)
    
    def proxy(self, purchases):
        self._proxy = purchases
    
    def needs_shipping(self):
        for purchase in self:
            if getattr(purchase.product.downcast(), 'needs_shipping', True):
                return True
        return False
    
    def add(self, purchase, save=True, calculate=True):
        self.ensure_state(ORDER_NEW)
        if self.pk is None:
            self.save()
        purchase.order = self
        if save:
            purchase.save()
            if calculate:
                self.calculate()

    def update(self, purchase, save=True, calculate=True):
        self.ensure_state(ORDER_NEW)
        if purchase.order != self:
            raise Exception("We don't own this purchase")
        if purchase.qty == 0:
            self.remove(purchase, save=False)
        if save:
            purchase.save()
            if calculate:
                self.calculate()

    def remove(self, purchase, save=True, calculate=True):
        self.ensure_state(ORDER_NEW)
        if purchase.order != self:
            raise Exception("We don't own this purchase")
        purchase.order = None
        if save:
            purchase.save()
            if calculate:
                self.calculate()

    def clear(self, save=True, calculate=True):
        self.ensure_state(ORDER_NEW)
        for purchase in self:
            self.remove(purchase, save=save, calculate=False)
        if save:
            if calculate:
                self.calculate()

    def calculate(self, subtotal=None, total=None, save=True):
        self.ensure_state(ORDER_NEW)
        
        if total is None:
            if subtotal is None:
                subtotal = Price()
                for purchase in self:
                    subtotal += purchase.total
            
            total = subtotal
            
            if self.shipment:
                total += self.shipment.costs
            if self.payment:
                total += self.payment.costs
                
            total = modules.pricing.get_price(
                price=total, order=self)

        if subtotal is None:
            subtotal = total
        
        self.subtotal = subtotal
        self.total = total
        
        # Update calculcated timestamp and save
        self.calculated = datetime.datetime.now()
        if save:
            self.save()

    def place(self):
        self.ensure_state(ORDER_NEW)
        if self.calculated is None:
            raise Exception("This order hasn't been calculated.")
        self.state = ORDER_PENDING
        self.number = modules.checkout.Order.generate_order_number(self)
        self.save()

    def cancel(self):
        self.state = ORDER_CANCELED
        self.save()

    def invalidate(self, force=False):
        if not force:
            self.ensure_state(ORDER_NEW)
        else:
            self.state = ORDER_NEW
        
        self.number = ''
        # ONLY Clear total
        # Clearing subtotal is not needed
        self.total = Price()
        self.calculated = None
        
        if self.shipment:
            self.shipment.delete()
        if self.payment:
            self.payment.delete()

        self.shipment = None
        self.payment = None
        self.save()

    # States

    @property
    def is_new(self):
        return self.state == ORDER_NEW

    @property
    def is_pending(self):
        return self.state == ORDER_PENDING

    @property
    def is_completed(self):
        return self.state == ORDER_COMPLETED

    @property
    def is_closed(self):
        return self.state == ORDER_CLOSED

    @property
    def is_canceled(self):
        return self.state == ORDER_CANCELED

    def ensure_state(self, state):
        if self.state != state:
            raise Exception("Not in state '{0}'".format(state))

    # Flags

    @property
    def may_cancel(self):
        return self.state == ORDER_PENDING and not self.paid

    @property
    def may_change(self):
        return self.state == ORDER_NEW

    @property
    def is_paid(self):
        return self.state != ORDER_NEW and self.total.amount == self.paid
        
    #
    
    def can_change_status(self, status):
        can_change = False
        statuses = modules.checkout.order_statuses
        
        # Verify new status
        if status not in statuses:
            raise Exception("Invalid order status '{0}'".format(status))
        
        # Lookup current status
        entry = statuses[self.status]
        config = entry[1] if len(entry) == 2 else {}
        if 'flow' in config:
            # Check against flow
            if status in config['flow']:
                can_change = True
        return can_change

    # Cleaning & saving

    def clean(self):
        old = None
        if self.pk:
            old = modules.checkout.Order.objects.get(pk=self.pk)
        if old is not None and self.status != old.status:
            if not old.can_change_status(self.status):
                raise ValidationError(
                    "Cannot transition order status "
                    "from '{0}' to '{1}'".format(old.status, self.status))
    
    def save(self, *args, **kwargs):
        old = None
        statuses = modules.checkout.order_statuses
        
        if self.pk:
            old = modules.checkout.Order.objects.get(pk=self.pk)

        # See if status is explicitly changed
        if old is not None and self.status != old.status:
            # Make sure this change is a valid flow
            if not old.can_change_status(self.status):
                raise Exception(
                    "Cannot transition order "
                    "status from '{0}' to '{1}'"
                    .format(old.status, self.status))

        # Check for new status
        status_changed = (
            old is None
            and self.status != statuses.initial
            or old is not None and self.status != old.status
        )

        # Check for new state
        state_changed = (
            old is None and self.state != ORDER_NEW
            or old is not None and self.state != old.state
        )

        # Check for now paid
        now_paid = (old is None or not old.is_paid) and self.is_paid
        
        # Get new status from new state
        if (not status_changed and state_changed and
                'on_{0}'.format(self.state) in
                statuses.event_to_status):
            self.status = statuses.event_to_status['on_{0}'.format(self.state)]

        # Get new status from on_paid
        if (not status_changed and now_paid and 
                'on_paid' in statuses.event_to_status):
            self.status = statuses.event_to_status['on_paid']

        # Get new state from new status
        if (not state_changed and status_changed and
                self.status in statuses.status_to_state):
            self.state = statuses.status_to_state[self.status]

        # Check for new status (again)
        status_changed = old is None or self.status != old.status

        # Check for new state (again)
        state_changed = old is None or self.state != old.state

        # At this point we save
        super(Order, self).save(*args, **kwargs)

        # Finally signal
        if status_changed:
            order_status_changed.send(
                sender=self, order=self, new_status=self.status,
                old_status=old.status if old else None)

        if state_changed:
            order_state_changed.send(
                sender=self, order=self, new_state=self.state,
                old_state=old.state if old else None)
            
            # Handle shortcuts
            if self.state == ORDER_PENDING:
                order_pending.send(sender=self, order=self)
            elif self.state == ORDER_COMPLETED:
                order_completed.send(sender=self, order=self)
            elif self.state == ORDER_CANCELED:
                order_canceled.send(sender=self, order=self)
            elif self.state == ORDER_CLOSED:
                order_closed.send(sender=self, order=self)

        if now_paid:
            order_paid.send(sender=self, order=self)

    # Overrides
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
        if self.number:
            return unicode(_(u"order #{0}").format(unicode(self.number)))
        else:
            return unicode(_(u"unplaced order"))

    class Meta:
        abstract = True
        verbose_name = _("order")
        verbose_name_plural = _("orders")
        ordering = ['-pk']


class Shipment(PolymorphicModel):
    
    def get_method(self):
        raise NotImplementedError()

    def __unicode__(self):
        return unicode(self.order)

    class Meta:
        abstract = True
        verbose_name = _("shipment")
        verbose_name_plural = _("shipments")


class Payment(PolymorphicModel):
    
    # Flags
    instant = True

    def get_method(self):
        raise NotImplementedError()

    def __unicode__(self):
        return unicode(self.order)

    class Meta:
        abstract = True
        verbose_name = _("payment")
        verbose_name_plural = _("payments")
