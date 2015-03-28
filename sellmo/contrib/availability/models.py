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

from datetime import timedelta, datetime

from django.db import models
from django.db.models import Q
from django.core.exceptions import ObjectDoesNotExist
from django.utils import timezone
from django.utils.translation import ugettext_lazy as _

from sellmo import modules
from sellmo.api.decorators import load


def _get_timedelta(value):
    if value is not None:
        return timedelta(**{
            modules.availability.time_defined_in: value
        })
    return timedelta()
    
    
@load(before='finalize_product_Product')
@load(after='finalize_availability_Backorder')
@load(after='finalize_availability_AvailabilityBase')
def load_model():
    class Product(modules.product.Product,
                   modules.availability.BackorderBase,
                   modules.availability.AvailabilityBase):
        
        supplier = models.ForeignKey(
            'availability.Supplier',
            null=True,
            blank=True,
            verbose_name=_("supplier")
        )
        
        def get_min_backorder_delay(self):
            a = super(Product, self).get_min_backorder_delay()
            b = timedelta()
            if self.supplier:
                b = self.supplier.get_min_backorder_delay()
            if a > b:
                return a
            else:
                return b
        
        def get_max_backorder_delay(self):
            a = super(Product, self).get_max_backorder_delay()
            b = timedelta()
            if self.supplier:
                b = self.supplier.get_max_backorder_delay()
            if a > b:
                return a
            else:
                return b
        
        def can_backorder(self):
            settings = modules.settings.get_settings()
            supplier_can_backorder = None
            if self.supplier is not None:
                supplier_can_backorder = self.supplier.can_backorder()
            return (self.allow_backorders is True or 
                    supplier_can_backorder or
                    settings.allow_backorders and 
                    self.allow_backorders is not False and
                    supplier_can_backorder is not False)
        
        def get_shipping_delay(self, stock=None, now=None):
            tz = timezone.get_current_timezone()
            
            if now is None:
                now = timezone.now()
            
            if stock is None:
                stock = self.stock
            
            settings = modules.settings.get_settings()
            min_delay = timedelta()
            max_delay = timedelta()
            
            # Apply any backorder delay
            if stock == 0 and self.can_backorder():
                min_delay += self.get_min_backorder_delay()
                max_delay += self.get_max_backorder_delay()
            elif stock == 0:
                return None
            
            # Get store availability
            try:
                nearest = settings.availability.get_nearest_availability()
            except ObjectDoesNotExist:
                pass
            else:
                # Get offset based of store availability
                offset = nearest.day - now.isoweekday()
                # Check against current time
                if (offset == 0 and nearest.available_from and
                        nearest.available_until and
                        nearest.available_until < now.time()):
                    offset = 7
                elif offset < 0:
                    offset = 7 + offset
                    
                # Apply store availablity offset
                min_delay += timedelta(days=offset)
                max_delay += timedelta(days=offset)
            
                if nearest.available_from:
                    dt = datetime.combine(now.date(), nearest.available_from)
                    dt = timezone.make_aware(dt, tz)
                    min_delay += dt - now
                if nearest.available_until:
                    dt = datetime.combine(now.date(), nearest.available_until)
                    dt = timezone.make_aware(dt, tz)
                    max_delay += dt - now
            
            return min_delay, max_delay
        
        class Meta(modules.product.Product.Meta,
                   modules.availability.BackorderBase.Meta,
                   modules.availability.AvailabilityBase.Meta):
            abstract = True
    
    modules.product.Product = Product
    
    
@load(before='finalize_variation_Variation')
@load(after='finalize_availability_AvailabilityBase')
def load_model():
    # Make sure variation module is present
    if not hasattr(modules, 'variation'):
        return
    
    class Variation(modules.variation.Variation,
                   modules.availability.AvailabilityBase):
        
        def get_shipping_delay(self, stock=None, now=None):
            if stock is None:
                stock = self.stock
            return self.product.get_shipping_delay(stock=stock, now=now)
        
        class Meta(modules.variation.Variation.Meta,
                   modules.availability.AvailabilityBase.Meta):
            abstract = True

    modules.variation.Variation = Variation


@load(action='finalize_availability_Backorder')
def finalize_model():
    pass


class BackorderBase(models.Model):
    
    allow_backorders = models.NullBooleanField(
        default=None,
        verbose_name=_("allow backorders")
    )
    
    min_backorder_time = models.PositiveSmallIntegerField(
        null=True,
        blank=True,
        verbose_name=_("minimum backorder time")
    )
    
    max_backorder_time = models.PositiveSmallIntegerField(
        null=True,
        blank=True,
        verbose_name=_("maximum backorder time")
    )
    
    def get_min_backorder_delay(self):
        return _get_timedelta(self.min_backorder_time)
    
    def get_max_backorder_delay(self):
        return _get_timedelta(self.max_backorder_time)
    
    def can_backorder(self):
        settings = modules.settings.get_settings()
        return (self.allow_backorders is True or 
                settings.allow_backorders and 
                self.allow_backorders is not False)
    
    class Meta:
        abstract = True


@load(action='finalize_availability_AvailabilityBase')
def finalize_model():
    pass


class AvailabilityBase(models.Model):

    stock = models.PositiveIntegerField(
        default=0,
        verbose_name=_("stock")
    )

    class Meta:
        abstract = True


@load(action='finalize_availability_Supplier')
@load(after='finalize_availability_Backorder')
def finalize_model():
    class Supplier(modules.availability.Supplier,
                   modules.availability.BackorderBase):

        class Meta(modules.availability.Supplier.Meta,
                   modules.availability.BackorderBase.Meta):
            app_label = 'availability'

    modules.availability.Supplier = Supplier


class Supplier(models.Model):

    name = models.CharField(
        max_length=80,
        verbose_name=_("name")
    )

    def __unicode__(self):
        return self.name

    class Meta:
        abstract = True
        verbose_name = _("supplier")
        verbose_name_plural = _("suppliers")
        
        
class StoreAvailabilityManager(models.Manager):
    
    def get_nearest_availability(self):
        available = self.filter(available=True)
        if not available:
            raise self.model.DoesNotExist()
        
        now = timezone.now()
        q = ((Q(available_from__isnull=True) |
            Q(available_from__lte=now.time())) &
            (Q(available_until__isnull=True) |
            Q(available_until__gte=now.time())))
        
        # Loop through days, beginnin with today ending with today
        first = True
        for day in range(now.isoweekday(), 8) + range(1, now.isoweekday() + 1):
            try:
                if first:
                    # Make sure today's time is checked
                    nearest = available.filter(q)
                    first = False
                else:
                    nearest = available.all()
                nearest = nearest.get(day=day)
            except self.model.DoesNotExist:
                continue
            else:
                return nearest
                
        raise self.model.DoesNotExist()
        
class StoreAvailability(models.Model):
    
    objects = StoreAvailabilityManager()
    
    day = models.PositiveSmallIntegerField(
        unique=True,
        choices=(
            (1, _("Monday")),
            (2, _("Tuesday")),
            (3, _("Wednesday")),
            (4, _("Thursday")),
            (5, _("Friday")),
            (6, _("Saturday")),
            (7, _("Sunday")),
        ),
        verbose_name=_("day")
    )
    
    available = models.BooleanField(
        default=True,
        verbose_name=_("available")
    )
    
    available_from = models.TimeField(
        null=True,
        blank=True,
        verbose_name=_("available from")
    )
    
    available_until = models.TimeField(
        null=True,
        blank=True,
        verbose_name=_("available until")
    )
    
    def __unicode__(self):
        return self.get_day_display()
    
    class Meta:
        abstract = True
        verbose_name = _("store availability")
        verbose_name_plural = _("store availability")
