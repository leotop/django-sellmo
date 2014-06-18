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
from sellmo import params
from sellmo.magic import ModelMixin
from sellmo.api.decorators import load

from django.db import models
from django.db.models.signals import m2m_changed, post_save, post_delete
from django.db.models.query import QuerySet
from django.db.models import Q, Max
from django.core.cache import cache
from django.core.urlresolvers import reverse
from django.utils.translation import ugettext_lazy as _

from mptt.models import MPTTModel, TreeForeignKey, TreeManager


@load(before='finalize_product_ProductRelatable')
def load_model():
    class ProductRelatable(modules.product.ProductRelatable):
        m2m_invalidations = (
            modules.product.ProductRelatable.m2m_invalidations +
            ['categories'])

        categories = models.ManyToManyField(
            'category.Category',
            related_name='%(app_label)s_%(class)s_related',
            blank=True,
        )

        def get_related_products_query(self):
            # Get categories including descendants
            q = Q()
            for category in self.categories.all():
                q |= Q(
                    categories__in=category.get_descendants(include_self=True))
            return (
                super(ProductRelatable, self).get_related_products_query() 
                | q)

        @classmethod
        def get_for_product_query(cls, product):
            # Get categories including ancestors
            q = Q()
            for category in product.categories.all():
                q |= Q(
                    categories__in=category.get_ancestors(include_self=True))
            return (
                super(ProductRelatable, cls).get_for_product_query(product)
                | q)

        @classmethod
        def sort_best_for_product(cls, product, matches):
            return super(ProductRelatable, cls).sort_best_for_product(
                product=product, matches=matches)

        class Meta(modules.product.ProductRelatable.Meta):
            abstract = True

    modules.product.ProductRelatable = ProductRelatable


# Cache invalidation
def on_cache_invalidation(sender, instance, **kwargs):
    cache_keys = cache.get('categories_cache_keys', [])
    cache.delete_many(cache_keys + ['navigation_cache_keys'])


@load(action='finalize_category_Category')
def finalize_model():

    class Category(modules.category.Category):

        class MPTTMeta(modules.category.Category.Meta):
            pass

        class Meta(modules.category.Category.Meta):
            app_label = 'category'

    # Hookup signals
    post_save.connect(on_cache_invalidation, sender=Category)
    post_delete.connect(on_cache_invalidation, sender=Category)

    modules.category.Category = Category


@load(after='finalize_product_Product')
def load_manager():

    qs = modules.product.Product.objects.get_query_set()

    class ProductQuerySet(qs.__class__):

        def in_category(self, category, recurse=True):
            if recurse:
                return self.filter(
                    categories__in=category.get_descendants(include_self=True))
            else:
                return self.filter(categories__in=[category])

    class ProductManager(modules.product.Product.objects.__class__):

        def in_category(self, *args, **kwargs):
            return self.get_query_set().in_category(*args, **kwargs)

        def get_query_set(self):
            return ProductQuerySet(self.model)

    class Product(ModelMixin):
        model = modules.product.Product
        objects = ProductManager()

    # Register
    modules.product.register('ProductQuerySet', ProductQuerySet)
    modules.product.register('ProductManager', ProductManager)


@load(after='finalize_category_Category')
def load_manager():
    if getattr(params, 'dumpdata', False):
        # Override manager with specialized dumpdata manager
        qs = modules.category.Category.objects.get_query_set()

        class CategoryQuerySet(qs.__class__):

            def order_by(self, *args, **kwargs):
                # Ignore pk ordering request by dumpdata command
                return super(CategoryQuerySet, self).order_by('tree_id', 'lft')

        class CategoryManager(modules.category.Category.objects.__class__):

            def get_query_set(self):
                return CategoryQuerySet(self.model)

        class Category(ModelMixin):
            model = modules.category.Category
            objects = CategoryManager()

        # Register
        modules.category.register('CategoryQuerySet', CategoryQuerySet)
        modules.category.register('CategoryManager', CategoryManager)


def on_categories_changed(sender, instance, action, reverse, pk_set, **kwargs):
    if action in ('post_add', 'post_remove'):
        if not reverse:
            instance.update_primary_category()
        else:
            for pk in pk_set:
                product = modules.product.Product.objects.get(pk=pk)
                product.update_primary_category()


@load(after='finalize_product_Product')
def load_model():
    if not getattr(params, 'loaddata', False):
        m2m_changed.connect(
            on_categories_changed,
            sender=modules.product.Product.categories.through)


@load(before='finalize_product_Product')
def load_model():
    class Product(modules.product.Product):

        def find_primary_category(self):
            q = self.categories.all().order_by('-level')
            if q:
                return q[0]
            return None

        def update_primary_category(self):
            if ((self.primary_category is None
                    or self.categories.filter(
                        pk=self.primary_category.pk).count() == 0)
                    and not getattr(self, '_primary_category_found', False)
                    and self.categories.count() > 0):
                # Find best suitable category
                found = self.find_primary_category()
                if self.primary_category != found:
                    self.primary_category = found
                    setattr(self, '_primary_category_found', True)
                    self.save()
            elif (not self.primary_category is None and 
                    self.categories.count() == 0):
                # Unassign
                self.primary_category = None
                setattr(self, '_primary_category_found', True)
                self.save()

        categories = models.ManyToManyField(
            'category.Category',
            blank=True,
            null=True,
            related_name='products',
            verbose_name=_("categories"),
        )

        primary_category = models.ForeignKey(
            'category.Category',
            blank=True,
            null=True,
            on_delete=models.SET_NULL,
            related_name='+',
            verbose_name=_("primary category"),
        )

        class Meta(modules.product.Product.Meta):
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

    def flat_ordered(self):
        return self.order_by('tree_id', 'lft')


class CategoryManager(TreeManager):

    def get_by_natural_key(self, full_slug):
        parts = full_slug.split('/')
        category = None
        for slug in parts:
            category = self.get(parent=category, slug=slug)
        return category

    def in_parent(self, *args, **kwargs):
        return self.get_query_set().in_parent(*args, **kwargs)

    def active(self, *args, **kwargs):
        return self.get_query_set().active(*args, **kwargs)

    def get_query_set(self):
        return CategoryQuerySet(self.model)


class Category(MPTTModel):

    objects = CategoryManager()

    sort_order = models.SmallIntegerField(
        default=0,
        verbose_name=_("sort order"),
    )

    parent = TreeForeignKey(
        'self',
        blank=True,
        null=True,
        verbose_name=_("parent category"),
        related_name='children'
    )

    name = models.CharField(
        max_length=255,
        verbose_name=_("name"),
    )

    slug = models.SlugField(
        max_length=80,
        db_index=True,
        verbose_name=_("slug"),
        help_text=_(
            "Slug will be used in the address of"
            " the category page. It should be"
            " URL-friendly (letters, numbers,"
            " hyphens and underscores only) and"
            " descriptive for the SEO needs."
        )
    )

    active = models.BooleanField(
        default=True,
        verbose_name=_("active"),
        help_text=(
            "Inactive categories will be hidden from the site."
        )
    )
    
    def get_descendants(self, *args, **kwargs):
        qs = modules.category.Category.objects.get_query_set()
        return super(Category, self).get_descendants(*args, **kwargs) \
                                    ._clone(klass=qs.__class__)
    
    def get_ancestors(self, *args, **kwargs):
        qs = modules.category.Category.objects.get_query_set()
        return super(Category, self).get_ancestors(*args, **kwargs) \
                                    ._clone(klass=qs.__class__)

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

    def get_absolute_url(self, slug=None):
        if slug is None:
            slug = self.full_slug
        return reverse('category.category', args=[slug])

    def natural_key(self):
        return (self.get_full_slug(),)

    def __unicode__(self):
        return self.full_name

    class MPTTMeta:
        order_insertion_by = ['sort_order', 'name']

    class Meta:
        abstract = True
        verbose_name = _("category")
        verbose_name_plural = _("categories")
    
