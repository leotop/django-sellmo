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


from decimal import Decimal

from sellmo import modules
from sellmo.api.decorators import load
from sellmo.api.pricing import Price

from django.db import models
from django.db.models.signals import post_save, pre_delete
from django.db.models.query import QuerySet
from django.utils.translation import ugettext_lazy as _


class QtyPriceQuerySet(QuerySet):

    def for_qty(self, qty):
        match = self.filter(qty__lte=qty).order_by('-qty').first()
        if match:
            return match
        raise self.model.DoesNotExist()


class QtyPriceManager(models.Manager):

    def get_queryset(self):
        return QtyPriceQuerySet(self.model, using=self._db)

    def for_qty(self, *args, **kwargs):
        return self.get_queryset().for_qty(*args, **kwargs)



class QtyPriceBase(models.Model):

    objects = QtyPriceManager()

    qty = models.PositiveIntegerField(
        verbose_name=_("quantity"),
        default=1,
    )

    def apply(self, price=None):
        raise NotImplementedError()

    def __unicode__(self):
        return unicode(_("{0} qty or more").format(self.qty))

    class Meta:
        ordering = ['qty']
        abstract = True


@load(after='finalize_qty_pricing_QtyPriceBase')
@load(before='finalize_qty_pricing_QtyPrice')
def load_model():
    class QtyPrice(
            modules.qty_pricing.QtyPrice,
            modules.qty_pricing.QtyPriceBase):

        amount = modules.pricing.construct_pricing_field(
            verbose_name=_("amount"),
        )

        def apply(self, price=None):
            return Price(self.amount)

        class Meta(
                modules.qty_pricing.QtyPrice.Meta,
                modules.qty_pricing.QtyPriceBase.Meta):
            abstract = True
    modules.qty_pricing.QtyPrice = QtyPrice



class QtyPrice(models.Model):

    class Meta:
        abstract = True


@load(after='finalize_qty_pricing_QtyPriceBase')
@load(before='finalize_qty_pricing_QtyPriceRatio')
def load_model():
    class QtyPriceRatio(
            modules.qty_pricing.QtyPriceRatio,
            modules.qty_pricing.QtyPriceBase):

        ratio = modules.pricing.construct_decimal_field(
            default=Decimal('1.0'),
            verbose_name=_("ratio"),
        )

        def apply(self, price=None):
            return price * self.ratio

        class Meta(
                modules.qty_pricing.QtyPriceRatio.Meta,
                modules.qty_pricing.QtyPriceBase.Meta):
            abstract = True

    modules.qty_pricing.QtyPriceRatio = QtyPriceRatio


class QtyPriceRatio(models.Model):

    class Meta:
        abstract = True


def on_invalidate_qty_price(sender, instance, **kwargs):
    #modules.pricing.get_index('product_price').update(product=[instance.product])
    print 'update qty price'


@load(action='finalize_qty_pricing_ProductQtyPrice')
@load(after='finalize_qty_pricing_QtyPrice')
def load_model():
    class ProductQtyPrice(
            modules.qty_pricing.ProductQtyPrice,
            modules.qty_pricing.QtyPrice):
        
        class Meta(modules.qty_pricing.ProductQtyPrice.Meta):
            app_label = 'pricing'

    modules.qty_pricing.ProductQtyPrice = ProductQtyPrice
    post_save.connect(on_invalidate_qty_price, sender=ProductQtyPrice)
    pre_delete.connect(on_invalidate_qty_price, sender=ProductQtyPrice)


class ProductQtyPrice(models.Model):

    product = models.ForeignKey(
        'product.Product',
        related_name='qty_prices',
        verbose_name=_("product"),
    )

    class Meta:
        abstract = True
        verbose_name = _("qty price")
        verbose_name_plural = _("qty prices")
