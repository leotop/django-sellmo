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


from sellmo import modules
from sellmo.api.decorators import load
from sellmo.core.polymorphism import (PolymorphicModel,
                                      PolymorphicManager,
                                      PolymorphicQuerySet,
                                      PolymorphicForeignKey)
from sellmo.api.checkout import ShippingMethod as _ShippingMethod

from django.db import models
from django.contrib.sites.models import Site
from django.utils.translation import ugettext_lazy as _


@load(action='finalize_shipping_Shipment')
@load(after='finalize_checkout_Shipment')
def finalize_model():
    class Shipment(modules.shipping.Shipment, modules.checkout.Shipment):
        
        class Meta(
                modules.shipping.Shipment.Meta,
                modules.checkout.Shipment.Meta):
            app_label = 'shipping'

    modules.shipping.Shipment = Shipment


class Shipment(models.Model):

    description = models.CharField(
        max_length=120,
        blank=True,
        verbose_name=_("description"),
    )
    
    carrier = models.ForeignKey(
        'shipping.ShippingCarrier',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name=_("carrier"),
    )
    
    method = PolymorphicForeignKey(
        'shipping.ShippingMethod',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name=_("carrier"),
    )
        
    def save(self, *args, **kwargs):
        if not self.description and self.method:
            self.description = self.method.name
            if self.carrier:
                self.description = _(u"{0} by {1}").format(
                    self.description, self.carrier.name)
    
        super(Shipment, self).save(*args, **kwargs)
    
    def get_method(self):
        if not self.method:
            raise Exception(
                "This shipment no longer has a shipping method.")
        for method in self.method.get_methods():
            if method.carrier == self.carrier:
                return method
        raise Exception("Shipping method could not be resolved.")
    
    def __unicode__(self):
        try:
            method = self.get_method()
        except Exception:
            pass
        else:
            return unicode(method)
        return self.description

    class Meta:
        abstract = True
        verbose_name = _("shipment")
        verbose_name_plural = _("shipments")


@load(action='finalize_shipping_ShippingMethod')
def finalize_model():
    class ShippingMethod(modules.shipping.ShippingMethod):

        class Meta(modules.shipping.ShippingMethod.Meta):
            app_label = 'shipping'

    modules.shipping.ShippingMethod = ShippingMethod


class ShippingMethod(PolymorphicModel):

    active = models.BooleanField(
        default=True,
        verbose_name=_("active"),
    )

    identifier = models.CharField(
        unique=True,
        db_index=True,
        max_length=20,
        verbose_name=_("identifier"),
    )

    name = models.CharField(
        max_length=80,
        verbose_name=_("name"),
    )
    
    carriers = models.ManyToManyField(
        'shipping.ShippingCarrier',
        blank=True,
        verbose_name=_("carriers")
    )

    def get_methods(self):
        if self.carriers.count() == 0:
            yield self.get_method()
        else:
            for carrier in self.carriers.all():
                yield self.get_method(carrier)

    def get_method(self, carrier=None):
        raise NotImplementedError()

    def __unicode__(self):
        return self.name

    class Meta:
        abstract = True
        verbose_name = _("shipping method")
        verbose_name_plural = _("shipping methods")


@load(action='finalize_shipping_ShippingCarrier')
def finalize_model():
    class ShippingCarrier(modules.shipping.ShippingCarrier):

        extra_costs = modules.pricing.construct_pricing_field(
            verbose_name=_("extra costs")
        )

        class Meta(modules.shipping.ShippingCarrier.Meta):
            app_label = 'shipping'

    modules.shipping.ShippingCarrier = ShippingCarrier


class ShippingCarrier(models.Model):

    active = models.BooleanField(
        default=True,
        verbose_name=_("active"),
    )

    identifier = models.CharField(
        unique=True,
        db_index=True,
        max_length=20,
        verbose_name=_("identifier"),
    )

    name = models.CharField(
        max_length=80,
        verbose_name=_("name"),
    )

    def __unicode__(self):
        return self.name

    class Meta:
        abstract = True
        verbose_name = _("shipping carrier")
        verbose_name_plural = _("shipping carriers")
