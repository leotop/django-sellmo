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


from django.db import models
from django.utils.translation import ugettext_lazy as _

from sellmo import modules
from sellmo.api.decorators import load
    
    
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
                    
        def ships_in(self):
            settings = modules.settings.get_settings()
            if self.stock > 0:
                pass
            elif self.can_backorder():
                pass
            else:
                return False
        
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
        default=1,
        verbose_name=_("minimum backorder time")
    )
    
    max_backorder_time = models.PositiveSmallIntegerField(
        default=1,
        verbose_name=_("maximum backorder time")
    )
    
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
        
        
class StoreAvailability(models.Model):
    
    day = models.PositiveSmallIntegerField(
        null=True,
        blank=True,
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
    
    class Meta:
        abstract = True
        verbose_name = _("store availability")
        verbose_name_plural = _("store availability")
