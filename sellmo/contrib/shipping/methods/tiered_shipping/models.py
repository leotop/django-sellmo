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
from sellmo.api.pricing import Price
from sellmo.contrib.shipping \
     .methods.tiered_shipping import (TieredShippingMethod as 
                                      _TieredShippingMethod)

from django.db import models
from django.db.models import Q
from django.db.models.query import QuerySet
from django.core.exceptions import ValidationError
from django.utils import six
from django.utils.functional import lazy
from django.utils.translation import ugettext_lazy as _


@load(after='finalize_shipping_ShippingMethod')
def load_subtypes():

    class TieredShippingMethod(modules.shipping.ShippingMethod):

        def get_method(self, carrier=None):
            name = self.name
            identifier = self.identifier
            if carrier:
                name = _(u"{0} by {1}").format(name, carrier.name)
                identifier = '{0}_{1}'.format(identifier, carrier.identifier)
            return _TieredShippingMethod(
                identifier, name, method=self, carrier=carrier)

        class Meta(modules.shipping.ShippingMethod.Meta):
            app_label = 'shipping'
            verbose_name = _("tiered shipping method")
            verbose_name_plural = _("tiered shipping methods")

    modules.shipping.register_subtype(TieredShippingMethod)


@load(action='finalize_shipping_TieredShippingTier')
def finalize_model():

    class TieredShippingTier(modules.shipping.TieredShippingTier):
        
        class Meta(modules.shipping.TieredShippingTier.Meta):
            app_label = 'shipping'

    modules.shipping.TieredShippingTier = TieredShippingTier


@load(before='finalize_shipping_TieredShippingTier')
def load_model():

    class TieredShippingTier(modules.shipping.TieredShippingTier):
        
        costs = modules.pricing.construct_pricing_field(
            verbose_name=_("shipping rate"),
        )
        
        min_amount = modules.pricing.construct_pricing_field(
            verbose_name=_("minimum amount"),
        )
        
        class Meta(modules.shipping.TieredShippingTier.Meta):
            abstract = True

    if modules.shipping.max_tier_attributes > 0:
        for i in range(modules.shipping.max_tier_attributes):
            TieredShippingTier.add_to_class(
                'max_value{0}'.format(i + 1),
                models.FloatField(
                    null=True,
                    blank=True,
                    verbose_name=get_attribute_name(i)
                )
            )

    modules.shipping.TieredShippingTier = TieredShippingTier


class TieredShippingTierQuerySet(QuerySet):

    def for_order(self, order):

        # Match against subtotal
        q = Q(min_amount__lte=order.subtotal.amount)

        if modules.shipping.max_tier_attributes > 0:
            # Match against attribute totals
            _settings = modules.settings.get_settings()
            for i in range(modules.shipping.max_tier_attributes):
                attribute = getattr(
                    _settings, 'shipping_tier_attribute{0}'.format(i + 1))
                # See if attribute is configured
                if attribute:
                    # Collect order total value for this attribute
                    total = 0
                    for purchase in order:
                        product = purchase.product.downcast()
                        value = product.attributes[attribute.key]
                        if value is not None:
                            total += value * purchase.qty

                    qargs = {
                        'max_value{0}__gte'.format(i + 1): total
                    }
                    q1 = Q(**qargs)

                    qargs = {
                        'max_value{0}__isnull'.format(i + 1): True
                    }
                    q2 = Q(**qargs)
                    q &= (q1 | q2)

        tiers = self.filter(q)
        if not tiers:
            raise self.model.DoesNotExist(
                "%s matching query does not exist." %
                self.model._meta.object_name
            )

        return tiers[0]


class TieredShippingTierManager(models.Manager):

    def for_order(self, *args, **kwargs):
        return self.get_queryset().for_order(*args, **kwargs)

    def get_queryset(self):
        return TieredShippingTierQuerySet(self.model, using=self._db)
        

class TieredShippingTier(models.Model):
    
    objects = TieredShippingTierManager()
    
    method = models.ForeignKey(
        'shipping.TieredShippingMethod',
        related_name='tiers'
    )
    
    class Meta:
        abstract = True
        verbose_name = _("tiered shipping tier")
        verbose_name_plural = _("tiered shipping tiers")
        ordering = ['costs']


def get_attribute_name(i):
    try:
        settings = modules.settings.get_settings()
    except Exception:
        attribute = None
    else:
        attribute = getattr(settings,
                            'shipping_tier_attribute{0}'.format(i + 1))
    
    if not attribute:
        attribute = _("value {0}".format(i + 1))
    
    return _(u"max {0}").format(attribute)

get_attribute_name = lazy(get_attribute_name, six.text_type)


@load(before='finalize_settings_SiteSettings')
def load_model():
    if modules.shipping.max_tier_attributes > 0:
        class SiteSettings(modules.settings.SiteSettings):

            def clean(self):
                valid_types = [
                    modules.attribute.Attribute.TYPE_INT,
                    modules.attribute.Attribute.TYPE_FLOAT,
                ]

                errors = {}
                for i in range(modules.shipping.max_tier_attributes):
                    attr = 'shipping_tier_attribute{0}'.format(i + 1)
                    attribute = getattr(self, attr, None)
                    if attribute and attribute.type not in valid_types:
                        errors[attr] = [
                            _("Invalid attribute type, must be numeric.")]

                if errors:
                    raise ValidationError(errors)

            class Meta(modules.settings.SiteSettings.Meta):
                abstract = True

        modules.settings.SiteSettings = SiteSettings
