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

from django.utils.translation import ugettext_lazy as _
from django.db import models
from django.db.models import Q
from django.db.models.query import QuerySet

#

from sellmo import modules
from sellmo.api.decorators import load
from sellmo.utils.polymorphism import PolymorphicModel

#

@load(action='load_product_subtypes', after='finalize_product_Product')
def load_product_subtypes():
    pass

@load(action='finalize_product_Product')
def finalize_model():
    
    class Product(modules.product.Product):
        class Meta:
            verbose_name = _("product")
            verbose_name_plural = _("products")
    
    modules.product.Product = Product
 
# Make sure to load directly after finalizing the product model
# Also ensure 'finalize_product_ProductRelatable' is called directly afterwards
@load(before='finalize_product_ProductRelatable', after='finalize_product_Product', directly=True)
def load_model():
    
    class ProductRelatable(modules.product.ProductRelatable):
        product = models.ManyToManyField(
            modules.product.Product,
            related_name = '+',
            blank = True,
        )
        
        class Meta:
            abstract = True
    
    modules.product.ProductRelatable = ProductRelatable


@load(action='finalize_product_ProductRelatable')
def finalize_model():
    pass

class Product(PolymorphicModel):
    
    slug = models.SlugField(
        max_length = 80,
        db_index = True,
        unique = True,
        verbose_name = _("slug"),
        help_text = _(
            "Slug will be used in the address of"
            " the product page. It should be"
            " URL-friendly (letters, numbers,"
            " hyphens and underscores only) and"
            " descriptive for the SEO needs."
        )
    )
    
    def __unicode__(self):
        return self.slug
        
    def natural_key(self):
        return (self.slug,)
        
    @models.permalink
    def get_absolute_url(self):
        return 'product.details', (self.slug,)
    
    def get_price(self, currency=None, **kwargs):
        return modules.pricing.get_price(product=self, currency=currency, **kwargs)
    
    class Meta:
        ordering = ['slug']
        app_label = 'product'
        abstract = True
        
class ProductRelatableQuerySet(QuerySet):
    def for_product(self, product):
        return self.filter(self.model.get_for_product_query(product=product)).distinct()
    
    def best_for_product(self, product):
        q = self.for_product(product)
        if q:
            return self.model.get_best_for_product(product=product, matches=q)
        raise self.model.DoesNotExist(
            "%s matching query does not exist." %
            self.model._meta.object_name) 
        
class ProductRelatableManager(models.Manager):
    def for_product(self, *args, **kwargs):
        return self.get_query_set().for_product(*args, **kwargs)
        
    def best_for_product(self, *args, **kwargs):
        return self.get_query_set().best_for_product(*args, **kwargs)
    
    def get_query_set(self):
        return ProductRelatableQuerySet(self.model)
        
class ProductRelatable(models.Model):
    objects = ProductRelatableManager()
    
    all_products = models.BooleanField(
        verbose_name = _("all products"),
    )
    
    @classmethod
    def get_for_product_query(cls, product):
        return Q(all_products=True) | Q(product=product)
        
    @classmethod
    def get_best_for_product(cls, product, matches):
        return [matches[0]]
    
    class Meta:
        abstract = True