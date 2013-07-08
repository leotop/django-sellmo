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
from sellmo.magic import ModelMixin, ManagerMixinHelper
from sellmo.api.decorators import load

#
from django.db import models
from django.db.models.signals import m2m_changed
from django.db.models.query import QuerySet
from django.db.models import Q, Max
from django.utils.translation import ugettext_lazy as _

#

from mptt.models import MPTTModel, TreeForeignKey, TreeManager

#

@load(after='finalize_category_Category', before='finalize_product_ProductRelatable')
def load_model():
    class ProductRelatable(modules.product.ProductRelatable):
        category = models.ManyToManyField(
            modules.category.Category,
            related_name = '+',
            blank = True,
        )
        
        @classmethod
        def get_for_product_query(cls, product):
            # Get categories including ancestors
            categories = []
            for category in product.category.all():
                categories += list(modules.category.Category.objects.filter(tree_id=category.tree_id, level__lte=category.level))
            
            return super(ProductRelatable, cls).get_for_product_query(product) | Q(category__in=categories)

        @classmethod
        def get_best_for_product(cls, product, matches):
            matches = matches.annotate(max_level=Max('category__level')).order_by('-max_level')
            return super(ProductRelatable, cls).get_best_for_product(product=product, matches=matches)

        class Meta:
            abstract = True

    modules.product.ProductRelatable = ProductRelatable

@load(action='finalize_category_Category')
def finalize_model():
    class Category(modules.category.Category):
        pass
    modules.category.Category = Category
    
@load(after='finalize_product_Product')
def load_manager():
    
    qs = modules.product.Product.objects.get_query_set()
    
    class ProductQuerySet(qs.__class__):
        def in_category(self, category, recurse=True):
            if recurse:
                return self.filter(category__in=category.get_descendants(include_self=True))
            else:
                return self.filter(category__in=[category])
    
    
    class ProductManager(modules.product.Product.objects.__class__, ManagerMixinHelper):
        def in_category(self, *args, **kwargs):
            return self.get_query_set().in_category(*args, **kwargs)
    
        def get_query_set(self):
            return ProductQuerySet(self.model)
    
    class Product(ModelMixin):
        model = modules.product.Product
        objects = ProductManager()

# Admin will not call "post_remove", this will cause an issue if all categories are unassigned.
def on_category_changed(sender, instance, action, **kwargs):
    if action == 'post_add' or action == 'post_remove':
        instance.update_primary_category(instance)
    
@load(after='finalize_product_Product')
def load_model():
    m2m_changed.connect(on_category_changed, sender=modules.product.Product.category.through)
    
@load(before='finalize_product_Product', after='finalize_category_Category')
def load_model():
    class Product(modules.product.Product):
        
        @staticmethod
        def find_primary_category(product):
            q = product.category.all().order_by('-level')
            if q:
                return q[0]
            return None
            
        @staticmethod
        def update_primary_category(product):
            
            if (product.primary_category is None 
            or getattr(product, '_primary_category_found', False) 
            or product.category.filter(pk=product.primary_category.pk).count() == 0
            ) and product.category.count() > 0:
                # Find best suitable category
                found = product.find_primary_category(product)
                if product.primary_category != found:
                    product.primary_category = found
                    setattr(product, '_primary_category_found', True)
                    product.save()
            elif not product.primary_category is None and product.category.count() == 0:
                # Unassign
                product.primary_category = None
                product.save()
        
        category = models.ManyToManyField(
            modules.category.Category,
            blank = True,
            null = True,
            related_name = 'products',
            verbose_name = _("category"),
        )
        
        primary_category = models.ForeignKey(
            modules.category.Category,
            blank = True,
            null = True,
            on_delete = models.SET_NULL,
            related_name = '+',
            verbose_name = _("primary category"),
        )
        
        class Meta:
            abstract = True
    
    modules.product.Product = Product
    
class CategoryQuerySet(QuerySet):
    def in_parent(self, category, recurse=True):
        q = self.filter(tree_id=category.tree_id)
        if recurse:
            return q.filter(level__gt=category.level)
        else:
            return q.filter(level=category.level + 1)
            
    def active(self):
        return self.filter(active=True)
        
    def root(self):
        return self.filter(level=0)
    
class CategoryManager(TreeManager):
    def in_parent(self, *args, **kwargs):
        return self.get_query_set().in_parent(*args, **kwargs)
        
    def active(self, *args, **kwargs):
        return self.get_query_set().active(*args, **kwargs)
        
    def root(self, *args, **kwargs):
        return self.get_query_set().root(*args, **kwargs)

    def get_query_set(self):
        return CategoryQuerySet(self.model)

class Category(MPTTModel):
    
    objects = CategoryManager()
    
    sort_order = models.SmallIntegerField(
        default = 0,
        verbose_name = _("sort order"),
    )
    
    parent = TreeForeignKey(
        'self',
        blank = True,
        null = True,
        verbose_name = _("parent category"),
        related_name = 'children'
    )
    
    name = models.CharField(
        max_length = 255,
        verbose_name = _("name"),
    )
    
    slug = models.SlugField(
        max_length = 80,
        db_index = True,
        verbose_name = _("slug"),
        help_text = _(
            "Slug will be used in the address of"
            " the category page. It should be"
            " URL-friendly (letters, numbers,"
            " hyphens and underscores only) and"
            " descriptive for the SEO needs."
        )
    )
    
    active = models.BooleanField(
        default = True,
        verbose_name = _("active"),
        help_text = (
            "Inactive categories will be hidden from the site."
        )
    )
    
    @property
    def descendants(self):
        qs = modules.category.Category.objects.get_query_set()
        return self.get_descendants()._clone(klass=qs.__class__)
        
    @property
    def ancestors(self):
        qs = modules.category.Category.objects.get_query_set()
        return self.get_ancestors()._clone(klass=qs.__class__)
        
    def get_full_name(self, ancestors=None):
        if ancestors is None:
            ancestors = self.get_ancestors(include_self=True)
        else:
            ancestors = ancestors + [self]
        return " | ".join(category.name for category in ancestors)
        
    full_name = property(get_full_name)
        
    def get_full_slug(self, ancestors=None):
        if ancestors is None:
            ancestors = self.get_ancestors(include_self=True)
        else:
            ancestors = ancestors + [self]
        return "/".join(category.slug for category in ancestors)
        
    full_slug = property(get_full_slug)
            
    @models.permalink
    def get_absolute_url(self, slug=None):
        if slug is None:
            slug = self.full_slug
        return 'category.category', (slug,)
    
    def __unicode__(self):
        return self.full_name
        
    class MPTTMeta:
        order_insertion_by = ['sort_order', 'name']
    
    class Meta:
        app_label = 'category'
        verbose_name = _("category")
        verbose_name_plural = _("categories")
        abstract = True
        
# Init modules
from sellmo.contrib.contrib_category.modules import *