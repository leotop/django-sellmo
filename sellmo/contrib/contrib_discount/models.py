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

from sellmo import modules
from sellmo.api.decorators import load
from sellmo.api.product.models import ProductRelatableManager, ProductRelatableQuerySet
from sellmo.core.polymorphism import PolymorphicModel, PolymorphicManager, PolymorphicQuerySet
from sellmo.magic import ModelMixin

#

from django.db import models
from django.db.models import Q
from django.utils.translation import ugettext_lazy as _

#

@load(action='load_discount_subtypes', after='finalize_discount_Discount')
def load_tax_subtypes():
    pass

# Make sure to load directly after finalize_discount_Discount and thus 
# directly after finalize_product_Product
@load(after='finalize_discount_Discount', directly=True)
def load_model():
    class ProductMixin(ModelMixin):
        model = modules.product.Product
        discount = models.ForeignKey(
            modules.discount.Discount,
            blank = True,
            null = True,
            on_delete = models.SET_NULL,
            related_name = 'products',
            verbose_name = _("discount"),
        )

# Make sure to load directly after finalize_product_ProductRelatable and thus 
# directly after finalize_product_Product          
@load(action='finalize_discount_Discount', after='finalize_product_ProductRelatable', directly=True)
def finalize_model():
    
    class DiscountQuerySet(ProductRelatableQuerySet, PolymorphicQuerySet):
        pass
    
    class DiscountManager(ProductRelatableManager, PolymorphicManager):
        def get_query_set(self):
            return DiscountQuerySet(self.model)
    
    class Discount(modules.discount.Discount, modules.product.ProductRelatable):
        
        objects = DiscountManager()
        
        @classmethod
        def get_for_product_query(cls, product):
            return super(Discount, cls).get_for_product_query(product) | Q(products=product)
            
        @classmethod
        def get_best_for_product(cls, product, matches):
            better = matches.filter(products=product)
            if better:
                matches = better
            return super(Discount, cls).get_best_for_product(product=product, matches=matches)
        
        class Meta(modules.discount.Discount.Meta):
            app_label = 'discount'
            verbose_name = _("discount")
            verbose_name_plural = _("discounts")
    
    modules.discount.Discount = Discount
    modules.discount.register('DiscountQuerySet', DiscountQuerySet)
    modules.discount.register('DiscountManager', DiscountManager)
        
class Discount(PolymorphicModel):
    
    name = models.CharField(
        max_length = 80,
        verbose_name = _("name"),
    )
    
    class Meta:
        abstract = True
    
    def __unicode__(self):
        return self.name            