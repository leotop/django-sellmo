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

from sellmo import modules
from sellmo.api.decorators import load
from sellmo.utils.polymorphism import PolymorphicModel, PolymorphicManager, PolymorphicQuerySet
from sellmo.api.checkout import ShippingMethod as _ShippingMethod

#

from django.db import models
from django.utils.translation import ugettext_lazy as _

#


@load(after='finalize_shipping_ShippingCarrier', before='finalize_shipping_ShippingMethod')
def load_model():
    class ShippingMethod(modules.shipping.ShippingMethod):
        
        carriers = models.ManyToManyField(
            modules.shipping.ShippingCarrier,
            blank = True,
            verbose_name = _("carriers")
        )
        
        class Meta:
            abstract = True
        
    modules.shipping.ShippingMethod = ShippingMethod

@load(action='finalize_shipping_ShippingMethod')
def finalize_model():
    class ShippingMethod(modules.shipping.ShippingMethod):
        class Meta:
            app_label = 'shipping'
            verbose_name = _("shipping method")
            verbose_name_plural = _("shipping methods")

    modules.shipping.ShippingMethod = ShippingMethod


class ShippingMethod(PolymorphicModel):
    
    active = models.BooleanField(
        default = True,
        verbose_name = _("active"),
    )
    
    identifier = models.CharField(
        unique = True,
        db_index = True,
        max_length = 20,
        verbose_name = _("identifier"),
    )
    
    description = models.CharField(
        max_length = 80,
        verbose_name = _("description"),
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
        return self.description

    class Meta:
        abstract = True

#

@load(action='finalize_shipping_ShippingCarrier')
def finalize_model():
    class ShippingCarrier(modules.shipping.ShippingCarrier):
        
        extra_costs = modules.pricing.construct_pricing_field(
            verbose_name = _("extra costs")
        )
        
        class Meta:
            app_label = 'shipping'
            verbose_name = _("shipping carrier")
            verbose_name_plural = _("shipping carriers")

    modules.shipping.ShippingCarrier = ShippingCarrier

class ShippingCarrier(models.Model):
    
    active = models.BooleanField(
        default = True,
        verbose_name = _("active"),
    )
    
    identifier = models.CharField(
        unique = True,
        db_index = True,
        max_length = 20,
        verbose_name = _("identifier"),
    )
    
    description = models.CharField(
        max_length = 80,
        verbose_name = _("description"),
    )
    
    def __unicode__(self):
        return self.description
    
    class Meta:
        abstract = True
    
# Init modules
from sellmo.contrib.contrib_shipping.modules import *
