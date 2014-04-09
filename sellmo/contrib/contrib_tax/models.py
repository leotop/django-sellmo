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
from sellmo.api.product.models import (ProductRelatableManager,
                                       ProductRelatableQuerySet)
from sellmo.core.polymorphism import (PolymorphicModel,
                                      PolymorphicManager,
                                      PolymorphicQuerySet)
from sellmo.magic import ModelMixin

from django.db import models
from django.db.models.signals import (pre_save,
                                      post_save,
                                      pre_delete,
                                      m2m_changed)
from django.db.models import Q
from django.contrib.sites.models import Site
from django.utils.translation import ugettext_lazy as _

#


@load(action='load_tax_subtypes', after='finalize_tax_Tax')
def load_tax_subtypes():
    pass


def on_tax_pre_save(sender, instance, **kwargs):
    if instance.pk is not None:
        old = instance.__class__.objects.get(pk=instance.pk)
        invalidate_indexes(old)


def on_tax_post_save(sender, instance, **kwargs):
    invalidate_indexes(instance)


def on_tax_m2m_changed(sender, instance, action, reverse, **kwargs):
    if action.startswith('post_'):
        if not reverse:
            invalidate_indexes(instance)
        else:
            modules.pricing.get_index(
                'product_price').update(product=[instance])


def on_tax_pre_delete(sender, instance, **kwargs):
    invalidate_indexes(instance)


def invalidate_indexes(tax):
    modules.pricing.get_index('product_price').update(
        product=modules.product.Product.objects.for_relatable(tax))


@load(after='load_tax_subtypes')
def hookup_invalidation():
    for relation in modules.tax.Tax.m2m_invalidations:
        field = getattr(modules.tax.Tax, relation)
        m2m_changed.connect(on_tax_m2m_changed, sender=field.through)
    for subtype in modules.tax.subtypes:
        pre_save.connect(on_tax_pre_save, sender=subtype)
        post_save.connect(on_tax_post_save, sender=subtype)
        pre_delete.connect(on_tax_pre_delete, sender=subtype)

# Make sure to load directly after finalize_product_ProductRelatable and thus
# directly after finalize_product_Product


@load(after='finalize_product_Product')
@load(after='finalize_product_ProductRelatable')
@load(action='finalize_tax_Tax')
def finalize_model():

    class TaxQuerySet(ProductRelatableQuerySet, PolymorphicQuerySet):
        pass

    class TaxManager(ProductRelatableManager, PolymorphicManager):

        def get_by_natural_key(self, name):
            return self.get(name=name)

        def get_query_set(self):
            return TaxQuerySet(self.model)

    class Tax(modules.tax.Tax, modules.product.ProductRelatable):

        objects = TaxManager()

        products = models.ManyToManyField(
            modules.product.Product,
            related_name='taxes',
            blank=True,
        )

        class Meta(
                modules.tax.Tax.Meta,
                modules.product.ProductRelatable.Meta):
            app_label = 'tax'
            verbose_name = _("tax")
            verbose_name_plural = _("taxes")

    modules.tax.Tax = Tax
    modules.tax.register('TaxQuerySet', TaxQuerySet)
    modules.tax.register('TaxManager', TaxManager)


class Tax(PolymorphicModel):

    name = models.CharField(
        max_length=80,
        verbose_name=_("name"),
        unique=True
    )

    def get_related_products_query(self):
        return super(Tax, self).get_related_products_query() | Q(taxes=self)

    def natural_key(self):
        return (self.name,)

    def apply(self, price):
        raise NotImplementedError()

    class Meta:
        abstract = True

    def __unicode__(self):
        return self.name
