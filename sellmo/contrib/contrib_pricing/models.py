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

from decimal import Decimal

#

from sellmo import modules
from sellmo.api.decorators import load
from sellmo.api.pricing import Price

#

from django.db import models
from django.db.models.signals import post_save, pre_delete
from django.db.models.query import QuerySet
from django.utils.translation import ugettext_lazy as _

#

from picklefield.fields import PickledObjectField

#

class QtyPriceQuerySet(QuerySet):
    def for_qty(self, qty):
        match = self.filter(qty__lte=qty).order_by('-qty').first()
        if match:
            return match
        match = self.all().order_by('qty').first()
        if match:
            return match
        raise self.model.DoesNotExist()

class QtyPriceManager(models.Manager):
    def get_query_set(self):
        return QtyPriceQuerySet(self.model)
        
    def for_qty(self, *args, **kwargs):
        return self.get_query_set().for_qty(*args, **kwargs)

#
    
@load(action='finalize_qty_pricing_QtyPriceBase')
def finalize_model():
    # No need to do anything, QtyPriceBase needs to remain abstract, we do need this action
    pass

class QtyPriceBase(models.Model):
    
    objects = QtyPriceManager()
    
    qty = models.PositiveIntegerField(
        verbose_name = _("quantity"),
        default = 1,
    )
    
    def apply(self, price=None):
        raise NotImplementedError()
    
    def __unicode__(self):
        return _("%s qty or more") % unicode(self.qty)
    
    class Meta:
        ordering = ['qty']
        abstract = True
        
@load(after='finalize_qty_pricing_QtyPriceBase', before='finalize_qty_pricing_QtyPrice')
def load_model():
    class QtyPrice(modules.qty_pricing.QtyPrice, modules.qty_pricing.QtyPriceBase):
        
        amount = modules.pricing.construct_pricing_field(
            verbose_name = _("amount"),
        )
        
        def apply(self, price=None):
            return Price(self.amount)
        
        class Meta(modules.qty_pricing.QtyPrice.Meta, modules.qty_pricing.QtyPriceBase.Meta):
            abstract =  True
    modules.qty_pricing.QtyPrice = QtyPrice
    
@load(action='finalize_qty_pricing_QtyPrice')
def finalize_model():
    # No need to do anything, QtyPrice needs to remain abstract, we do need this action
    pass

class QtyPrice(models.Model):
    class Meta:
        abstract = True
        
@load(after='finalize_qty_pricing_QtyPriceBase', before='finalize_qty_pricing_QtyPriceRatio')
def load_model():
    class QtyPriceRatio(modules.qty_pricing.QtyPriceRatio, modules.qty_pricing.QtyPriceBase):
        
        ratio = modules.pricing.construct_decimal_field(
            default = Decimal('1.0'),
            verbose_name = _("ratio"),
        )
        
        def apply(self, price=None):
            return price * self.ratio
        
        class Meta(modules.qty_pricing.QtyPriceRatio.Meta, modules.qty_pricing.QtyPriceBase.Meta):
            abstract =  True
            
    modules.qty_pricing.QtyPriceRatio = QtyPriceRatio
    
@load(action='finalize_qty_pricing_QtyPriceRatio')
def finalize_model():
    # No need to do anything, QtyPriceBase needs to remain abstract, we do need this action
    pass
        
class QtyPriceRatio(models.Model):
    class Meta:
        abstract = True
        
def on_invalidate_index(sender, instance, **kwargs):
    modules.pricing.get_index('product_price').update(product=[instance.product])
        
@load(action='finalize_qty_pricing_ProductQtyPrice')
def finalize_model():
    class ProductQtyPrice(modules.qty_pricing.ProductQtyPrice):
        class Meta(modules.qty_pricing.ProductQtyPrice.Meta):
            app_label = 'pricing'
            verbose_name = _("qty price")
            verbose_name_plural = _("qty prices")
    
    modules.qty_pricing.ProductQtyPrice = ProductQtyPrice
    post_save.connect(on_invalidate_index, sender=ProductQtyPrice)
    pre_delete.connect(on_invalidate_index, sender=ProductQtyPrice)
    
    
@load(before='finalize_qty_pricing_ProductQtyPrice')
@load(after='finalize_qty_pricing_QtyPrice')
@load(after='finalize_product_Product')
def load_model():
    class ProductQtyPrice(modules.qty_pricing.ProductQtyPrice, modules.qty_pricing.QtyPrice):
        product = models.ForeignKey(
            modules.product.Product,
            related_name = 'qty_prices',
            verbose_name = _("product"),
        )
        
        class Meta(modules.qty_pricing.ProductQtyPrice.Meta):
            abstract = True
    
    modules.qty_pricing.ProductQtyPrice = ProductQtyPrice

class ProductQtyPrice(models.Model):
    class Meta:
        abstract = True
        
# Setup indexes
@load(after='finalize_product_Product')
def setup_indexes():
    index = modules.pricing.get_index('product_price')
    index.add_kwarg('qty', models.PositiveIntegerField(
        null = True
    ), required = False)
    
class PriceIndexHandle(models.Model):
    
    index = models.CharField(
        max_length = 255,
        unique = True,
        verbose_name = _("index"),
    )
    
    updates = PickledObjectField(
        editable = False,
        null = True
    )
    
    class Meta:
        abstract = True
        
@load(action='finalize_price_indexing_PriceIndexHandle')
def finalize_model():
    class PriceIndexHandle(modules.price_indexing.PriceIndexHandle):
        class Meta(modules.price_indexing.PriceIndexHandle.Meta):
            app_label = 'pricing'
            verbose_name = _("price index")
            verbose_name_plural = _("price indexes")

    modules.price_indexing.PriceIndexHandle = PriceIndexHandle
