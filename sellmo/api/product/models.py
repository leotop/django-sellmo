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


from django.db import models
from django.db.models import Q
from django.db.models.query import QuerySet
from django.db.models.signals import (pre_save, pre_delete, post_save, 
                                      m2m_changed)
from django.utils.translation import ugettext_lazy as _

from sellmo import modules
from sellmo.api.decorators import load
from sellmo.core.polymorphism import (PolymorphicModel, PolymorphicManager, 
                                      PolymorphicQuerySet)


@load(action='load_product_subtypes')
@load(after='finalize_product_Product')
def load_product_subtypes():
    pass


def get_indexable_products():
    return modules.product.Product.objects.all()


@load(action='finalize_product_Product')
def finalize_model():
    class Product(modules.product.Product):

        class Meta(modules.product.Product.Meta):
            app_label = 'product'
            verbose_name = _("product")
            verbose_name_plural = _("products")

    modules.product.Product = Product
    index = modules.pricing.create_index('product_price')
    index.add_kwarg(
        'product',
        models.ForeignKey(Product),
        default=get_indexable_products,
        model=Product
    )


class ProductQuerySet(PolymorphicQuerySet):

    def for_relatable(self, relatable):
        return self.filter(pk__in=relatable.get_related_products())


class ProductManager(PolymorphicManager):

    def __init__(self, cls=ProductQuerySet, **kwargs):
        super(ProductManager, self).__init__(cls=cls, **kwargs)

    def for_relatable(self, *args, **kwargs):
        return self.get_query_set().for_relatable(*args, **kwargs)

    def get_by_polymorphic_natural_key(self, slug):
        return self.get(slug=slug)


class Product(PolymorphicModel):

    objects = ProductManager()

    #

    slug = models.SlugField(
        max_length=80,
        db_index=True,
        unique=True,
        verbose_name=_("slug"),
        help_text=_(
            "Slug will be used in the address of"
            " the product page. It should be"
            " URL-friendly (letters, numbers,"
            " hyphens and underscores only) and"
            " descriptive for the SEO needs."
        )
    )

    def __unicode__(self):
        return self.slug

    def polymorphic_natural_key(self):
        return (self.slug,)

    @models.permalink
    def get_absolute_url(self):
        return 'product.details', (self.slug,)

    class Meta:
        ordering = ['slug']
        abstract = True


class ProductRelatableQuerySet(QuerySet):

    def for_product(self, product):
        return self.filter(self.model.get_for_product_query(product=product)) \
                   .distinct()

    def best_for_product(self, product):
        matches = self.for_product(product)
        if matches:
            return self.model.get_best_for_product(
                product=product, matches=matches)
        raise self.model.DoesNotExist(
            "{0} matching query does not exist.".format(
            self.model._meta.object_name))


class ProductRelatableManager(models.Manager):

    def for_product(self, *args, **kwargs):
        return self.get_query_set().for_product(*args, **kwargs)

    def best_for_product(self, *args, **kwargs):
        return self.get_query_set().best_for_product(*args, **kwargs)

    def get_query_set(self):
        return ProductRelatableQuerySet(self.model)


class ProductRelatable(models.Model):
    objects = ProductRelatableManager()
    m2m_invalidations = ['products']

    all_products = models.BooleanField(
        default=False,
        verbose_name=_("all products"),
    )

    def get_related_products(self):
        products = modules.product.Product.objects.get_query_set()
        if self.all_products:
            return products.all()
        else:
            return products.filter(self.get_related_products_query())

    def get_related_products_query(self):
        return Q()

    @classmethod
    def get_for_product_query(cls, product):
        return Q(all_products=True) | Q(products=product)

    @classmethod
    def sort_best_for_product(cls, product, matches):
        return matches.order_by('all_products')

    @classmethod
    def get_best_for_product(cls, product, matches):
        return cls.sort_best_for_product(product, matches)[0]

    class Meta:
        abstract = True
