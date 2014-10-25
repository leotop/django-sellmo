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


from sellmo import modules, celery, params
from sellmo.api.decorators import load
from sellmo.magic import ModelMixin
from sellmo.utils.formatting import call_or_format
from sellmo.core.polymorphism import PolymorphicModel, PolymorphicManager
from sellmo.contrib.variation import tasks
from sellmo.contrib.variation.variant import (VariantFieldDescriptor,
                                                      VariantMixin,
                                                      get_differs_field_name)
from sellmo.contrib.variation.utils import generate_slug
from sellmo.contrib.variation.signals import (variations_invalidating,
                                                      variations_invalidated)
from sellmo.contrib.variation.helpers import (AttributeHelper,
                                                      VariantAttributeHelper,
                                                      VariationAttributeHelper)
from sellmo.contrib.attribute.query import product_q, value_q

from django.db import models, transaction, IntegrityError
from django.db.models import Q, F, Count
from django.db.models.query import QuerySet
from django.db.models.signals import pre_save, post_save, pre_delete
from django.core.exceptions import ValidationError
from django.contrib.contenttypes.models import ContentType
from django.utils.translation import ugettext_lazy as _

import sys
import logging
import itertools


logger = logging.getLogger('sellmo')


@load(action='setup_variants')
@load(after='load_product_subtypes')
def setup_variants():
    pass


@load(before='finalize_product_Product')
def load_model():
    class Product(modules.product.Product):

        def __init__(self, *args, **kwargs):
            super(Product, self).__init__(*args, **kwargs)
            self.attributes = AttributeHelper(self)

        def save(self, *args, **kwargs):
            super(Product, self).save(*args, **kwargs)

            # Try to update variants
            downcasted = self.downcast()
            if (hasattr(downcasted, 'variants')
                    and downcasted.variants.count() > 0):
                for variant in downcasted.variants.all():
                    variant.save()

        class Meta(modules.product.Product.Meta):
            abstract = True

    modules.product.Product = Product


@load(after='finalize_product_Product')
def load_manager():

    qs = modules.product.Product.objects.get_queryset()

    class ProductQuerySet(qs.__class__):
        
        def _get_prefetched_values(self):
            return super(ProductQuerySet, self) \
                        ._get_prefetched_values() \
                        .filter(variates=False)
        
        def variants(self, exclude=False, only=False):
            if exclude:
                return self.filter(
                    content_type__in=ContentType.objects.get_for_models(
                        *modules.product.subtypes).values())
            if only:
                return self.filter(
                    content_type__in=ContentType.objects.get_for_models(
                        *modules.variation.subtypes).values())
            return self

    class ProductManager(modules.product.Product.objects.__class__):

        def get_queryset(self):
            return ProductQuerySet(self.model, using=self._db)

        def variants(self, *args, **kwargs):
            return self.get_queryset().variants(*args, **kwargs)

    class Product(ModelMixin):
        model = modules.product.Product
        objects = ProductManager()

    modules.product.register('ProductQuerySet', ProductQuerySet)
    modules.product.register('ProductManager', ProductManager)


@load(after='load_variants')
def load_model():
    for subtype in modules.variation.product_subtypes:
        class Product(ModelMixin):
            model = subtype
            
            def get_grouped_by(self):
                try:
                    return modules.attribute.Attribute.objects \
                                  .which_variate(self).get(groups=True)
                except modules.attribute.Attribute.DoesNotExist:
                    return None
            
            def get_variated_by(self):
                return modules.attribute.Attribute.objects.which_variate(self)

            def get_variations(self, invalidated=False):
                if getattr(self, '_is_variant', False):
                    return modules.variation.Variation.objects \
                                  .for_product(
                                    self.product, invalidated=invalidated) \
                                  .filter(variant=self)
                return modules.variation.Variation.objects \
                              .for_product(self, invalidated=invalidated)


@load(action='load_variants')
@load(after='setup_variants')
@load(after='finalize_variation_Variant')
def load_variants():
    for subtype in modules.variation.product_subtypes:
        class Meta(subtype.Meta):
            app_label = 'product'
            verbose_name = _("variant")
            verbose_name_plural = _("variants")

        name = '{0}Variant'.format(subtype.__name__)
        attr_dict = {
            'product': models.ForeignKey(
                subtype,
                related_name='variants',
                editable=False
            ),
            'Meta': Meta,
            '__module__': subtype.__module__
        }

        model = type(
            name,
            (VariantMixin, modules.variation.Variant, subtype,),
            attr_dict)
        
        model.setup()
        modules.variation.subtypes.append(model)
        setattr(modules.variation, name, model)


@load(action='finalize_variation_Variant')
def finalize_model():

    class Variant(modules.variation.Variant):

        def __init__(self, *args, **kwargs):
            super(Variant, self).__init__(*args, **kwargs)
            self.attributes = VariantAttributeHelper(self)

        price_adjustment = modules.pricing.construct_pricing_field(
            verbose_name=_("price adjustment")
        )

        class Meta(modules.variation.Variant.Meta):
            abstract = True

    modules.variation.Variant = Variant


class Variant(models.Model):

    def __unicode__(self):
        prefix = super(Variant, self).__unicode__()
        if prefix != unicode(self.product):
            return prefix
        return modules.variation.generate_variation_description(
            prefix=prefix, values=self.values.all())

    class Meta:
        abstract = True


def on_value_pre_save(sender, instance, raw=False, *args, **kwargs):
    if not raw:
        product = instance.product.downcast()
        instance.base_product = None
        if getattr(product, '_is_variant', False):
            instance.base_product = product.product


def on_value_post_save(sender, instance, raw=False, *args, **kwargs):
    if not raw:
        modules.variation.Variation.objects.invalidate(
            instance.base_product if 
            instance.base_product else instance.product)


def on_value_pre_delete(sender, instance, *args, **kwargs):
    modules.variation.Variation.objects.invalidate(
        instance.base_product if
        instance.base_product else instance.product)


@load(after='finalize_attribute_Value')
def listen():
    pre_save.connect(on_value_pre_save, sender=modules.attribute.Value)
    post_save.connect(on_value_post_save, sender=modules.attribute.Value)
    pre_delete.connect(on_value_pre_delete, sender=modules.attribute.Value)


@load(after='finalize_attribute_Attribute')
def load_manager():

    qs = modules.attribute.Attribute.objects.get_queryset()

    class AttributeQuerySet(qs.__class__):

        def for_product_or_variants_of(self, product):
            return (self.filter(Q(values__product=product)
                    | Q(values__base_product=product)).distinct())

        def which_variate(self, product):
            return self.filter(
                Q(variates=True) &
                (Q(values__base_product=product) | 
                 Q(values__product=product) &
                 Q(values__variates=True))).distinct()

    class AttributeManager(modules.attribute.Attribute.objects.__class__):

        def get_queryset(self):
            return AttributeQuerySet(self.model, using=self._db)

        def for_product_or_variants_of(self, *args, **kwargs):
            return self.get_queryset() \
                       .for_product_or_variants_of(*args, **kwargs)

        def which_variate(self, *args, **kwargs):
            return self.get_queryset().which_variate(*args, **kwargs)

    class Attribute(ModelMixin):
        model = modules.attribute.Attribute
        objects = AttributeManager()

    modules.attribute.register('AttributeQuerySet', AttributeQuerySet)
    modules.attribute.register('AttributeManager', AttributeManager)


@load(before='finalize_attribute_Attribute')
def load_model():

    class Attribute(modules.attribute.Attribute):

        variates = models.BooleanField(
            default=False,
            verbose_name=_("variates")
        )

        groups = models.BooleanField(
            default=False,
            verbose_name=_("groups")
        )

        def save(self, *args, **kwargs):
            old = None
            if self.pk:
                old = modules.attribute.Attribute.objects.get(pk=self.pk)
            super(Attribute, self).save(*args, **kwargs)
            if self.variates or old and old.variates:
                products = modules.product.Product.objects.filter(
                        product_q(attribute=self,
                                 through='base_product'))
                modules.variation.Variation.objects.invalidate(
                    products=products)

        class Meta(modules.attribute.Attribute.Meta):
            abstract = True

    modules.attribute.Attribute = Attribute


@load(after='finalize_attribute_Value')
def load_manager():

    qs = modules.attribute.Value.objects.get_queryset()

    class ValueQuerySet(qs.__class__):

        def for_product_or_variants_of(self, product):
            q = Q(product=product) | Q(base_product=product)
            return self.filter(q)

        def which_variate(self, product):
            return self.filter(
                Q(attribute__variates=True) &
                (Q(base_product=product) |
                 Q(product=product) & 
                 Q(variates=True)))

    class ValueManager(modules.attribute.Value.objects.__class__):

        def get_queryset(self):
            return ValueQuerySet(self.model, using=self._db)

        def for_product_or_variants_of(self, *args, **kwargs):
            return self.get_queryset() \
                       .for_product_or_variants_of(*args, **kwargs)

        def which_variate(self, *args, **kwargs):
            return self.get_queryset().which_variate(*args, **kwargs)

    class Value(ModelMixin):
        model = modules.attribute.Value
        objects = ValueManager()

    modules.attribute.register('ValueQuerySet', ValueQuerySet)
    modules.attribute.register('ValueManager', ValueManager)


@load(before='finalize_attribute_Value')
def load_model():

    class Value(modules.attribute.Value):

        base_product = models.ForeignKey(
            'product.Product',
            db_index=True,
            null=True,
            blank=True,
            editable=False,
            related_name='variant_values'
        )

        variates = models.BooleanField(
            default=False,
            editable=False
        )

        class Meta(modules.attribute.Value.Meta):
            abstract = True

    modules.attribute.Value = Value


@load(action='finalize_variation_Variation')
def finalize_model():

    class Variation(modules.variation.Variation):
        
        class Meta(modules.variation.Variation.Meta):
            app_label = 'variation'

    modules.variation.Variation = Variation


class VariationQuerySet(QuerySet):

    def for_product(self, product):
        return self.filter(product=product)


class VariationManager(models.Manager):

    @transaction.atomic
    def build(self, product):
        product = product.downcast()
        
        # Get all variating attributes for this product
        attributes = modules.attribute.Attribute.objects.which_variate(product)

        # Do we have an attribute which groups ?
        group = attributes.filter(groups=True).first()

        # CONVERT TO LIST FOR PERFORMANCE AND INDEXING
        attributes = list(attributes)
        
        if attributes:
            # Create all possible variation combinations
            combinations = itertools.product(*[
                (modules.attribute.get_sorted_values(
                    values=(modules.attribute.Value.objects
                        .which_variate(product)
                        .for_attribute(attribute)
                        .attribute_values()
                        .distinct()),
                    attribute=attribute,
                    product=product))
                for attribute in attributes])
        else:
            combinations = []
        
        # Create variations
        sort_order = 0
        created = []
        for combination in combinations:
            
            # Find all values which could be in this combination.
            # Values can be explicitly assigned to a variant, or 
            # they could variate this product.
            values = Q()
            for attribute, value in zip(attributes, combination):
                values |= value_q(attribute, value)
        
            values = (modules.attribute.Value.objects
                        .which_variate(product)
                        .filter(values))
                        
            # Filter implicit values
            implicits = values.filter(variates=True)
            
            # Find all remaining variants which can be matched
            # against the values in this combination.
            variants = product.variants.filter(
                pk__in=(values.exclude(product=product)
                    .order_by('product')
                    .distinct()
                    .values('product')))
                                        
            # Find most explicit value combination
            explicits = modules.attribute.Value.objects.none()
            for variant in variants:
                current = values.filter(product=variant)
                if current.count() > explicits.count():
                    explicits = current
                    
            # Resolve variant
            variant = product if not explicits else explicits[0].product.downcast()
            
            # Resolve actual values
            if variant == product:
                # All values are implicit  since we don't have a variant
                values = implicits
            else:
                # Collect all values by comining implicit and explicits
                implicits = implicits.exclude(attribute__in=explicits
                    .values('attribute'))
                values = values.filter(Q(pk__in=implicits) | Q(pk__in=explicits))
            
            # See if this is a valid values combination
            if values.count() != len(combination):
                if values.count() > len(combination):
                    logger.warning("Invalid variation values {0} for "
                                   "product {1}.".format(values, product))
                continue
            
            # Generate a unique key (uses slug format) for this variation 
            variation_key = generate_slug(product=variant, values=values, 
                                          full=True, unique=False)
            
            # Generate description (does not use all values only implicits).
            # This because unicode(variant) also calls upon 
            # generate_variation_description() with it's own explicit values.
            variation_description = modules.variation \
                .generate_variation_description(prefix=unicode(variant),
                                                values=implicits)
            
            try:
                # See if variation already exists
                variation = modules.variation.Variation.objects.get(
                    id=variation_key,
                    product=product)
            except modules.variation.Variation.DoesNotExist:
                # Create
                variation = modules.variation.Variation.objects.create(
                    id=variation_key,
                    description=variation_description,
                    product=product,
                    variant=variant,
                    sort_order=sort_order
                )
            else:
                # Update
                variation.variant = variant
                variation.sort_order = sort_order
                variation.description = variation_description
                variation.save()
            
            variation.values.add(*values)
            sort_order += 1
            
            # Make sure this variation does not get deleted
            created.append(variation_key)

        # Handle grouping
        if group:
            # We need to find a single variant which is common across all
            # variations in this group
            for value in modules.attribute.Value.objects \
                                .which_variate(product) \
                                .for_attribute(attribute=group) \
                                .attribute_values() \
                                .distinct():
                
                # Get variations for this grouped attribute / value combination
                qargs = {
                    'values__attribute': group,
                    'values__{0}'.format(group.value_field): value,
                }
                variations = modules.variation.Variation.objects.filter(
                    product=product).filter(**qargs)
                
                # Get variant
                qargs = [product_q(group, value)]
                if variations.count() > 1:
                    # Get single variant common across all variations
                    for attribute in attributes:
                        if attribute != group:
                            qargs.append(~product_q(attribute))
                
                try:
                    variant = product.variants.get(*qargs)
                except modules.product.Product.DoesNotExist:
                    variant = product
                except modules.product.Product.MultipleObjectsReturned:
                    variant = product
                    logger.warning("Product {product} has multiple variants "
                                   "which conflict with the following "
                                   "attribute/value combinations: "
                                   "{attribute}/{value}"
                                   .format(product=product,
                                           attribute=group,
                                           value=value))

                variations.update(group_variant=variant)

        # Delete any stale variations
        stale = self.filter(product=product) \
                    .exclude(pk__in=created)
        stale.delete()

        # Finally update product
        product.variations_invalidated = False

    def invalidate(self, products):
        if isinstance(products, modules.product.Product):
            products = [products]
        if celery.enabled and not getattr(params, 'worker_mode', False):
            tasks.invalidate_variations.apply_async((products,))
        else:
            for product in products:
                if not product.variations_invalidated:
                    variations_invalidating.send(self, product=product)
                    product.variations_invalidated = True
                    variations_invalidated.send(self, product=product)

    def get_queryset(self):
        return VariationQuerySet(self.model, using=self._db)

    def for_product(self, product, invalidated=False):
        product = product.downcast()
        
        # Capture IntegrityError's as these are caused by concurrency.
        # Output will always be valid due to transactions.
        def build():
            try:
                self.build(product)
            except IntegrityError as ex:
                pass
        
        if True or not invalidated and product.variations_invalidated:
            # Variations invalidated, rebuild
            build()
        
        # Get variations
        variations = self.get_queryset().for_product(product)

        if not invalidated and variations.count() == 0:
            # No variations, build
            build()
            variations = self.get_queryset().for_product(product)

        return variations


class Variation(models.Model):

    objects = VariationManager()

    def __init__(self, *args, **kwargs):
        super(Variation, self).__init__(*args, **kwargs)
        self.attributes = VariationAttributeHelper(self)
    
    id = models.CharField(
        max_length=255,
        primary_key=True,
        editable=False,
    )
    
    # The product we are based on
    product = models.ForeignKey(
        'product.Product',
        db_index=True,
        editable=False,
        related_name='+',
        verbose_name=_("product"),
    )
    
    # The variant we are based on (can be product)
    variant = models.ForeignKey(
        'product.Product',
        db_index=True,
        editable=False,
        related_name='+',
        verbose_name=_("variant"),
    )
    
    # The variant we are based on and which is common across every
    # variation in the group (can be a product)
    group_variant = models.ForeignKey(
        'product.Product',
        db_index=True,
        editable=False,
        null=True,
        related_name='+',
        verbose_name=_("group variant"),
    )
    
    values = models.ManyToManyField(
        'attribute.Value',
        editable=False,
        related_name='+',
        verbose_name=_("values"),
    )

    sort_order = models.SmallIntegerField(
        verbose_name=_("sort order"),
        editable=False,
    )

    description = models.CharField(
        verbose_name=_("description"),
        max_length=255,
        editable=False,
    )

    def __unicode__(self):
        return self.description

    class Meta:
        abstract = True
        ordering = ['sort_order']
        verbose_name = _("variation")
        verbose_name_plural = _("variations")


@load(action='finalize_variation_VariationsState')
def finalize_model():

    class VariationsState(modules.variation.VariationsState):
        
        class Meta(modules.variation.VariationsState.Meta):
            app_label = 'variation'

    modules.variation.VariationsState = VariationsState


@load(before='finalize_product_Product')
def load_model():

    class Product(modules.product.Product):

        def get_variations_invalidated(self):
            try:
                variations_state = self.variations_state
            except modules.variation.VariationsState.DoesNotExist:
                variations_state = modules.variation.VariationsState.objects \
                                          .create(product=self)
            return variations_state.invalidated

        def set_variations_invalidated(self, value):
            try:
                variations_state = self.variations_state
            except modules.variation.VariationsState.DoesNotExist:
                variations_state = modules.variation.VariationsState.objects \
                                          .create(product=self)
            variations_state.invalidated = value
            variations_state.save()

        variations_invalidated = property(get_variations_invalidated,
                                          set_variations_invalidated)

        class Meta(modules.product.Product.Meta):
            abstract = True

    modules.product.Product = Product


class VariationsState(models.Model):

    invalidated = models.BooleanField(
        default=False,
        editable=False,
    )
    
    product = models.OneToOneField(
        'product.Product',
        editable=False,
        related_name='variations_state'
    )
    
    def __unicode__(self):
        return unicode(self.product)

    class Meta:
        abstract = True
        verbose_name = _("variations state")
        verbose_name_plural = _("variations states")


class VariationPurchase(models.Model):

    variation_key = models.CharField(
        max_length=255
    )

    def merge_with(self, purchase):
        super(VariationPurchase, self).merge_with(purchase)

    def clone(self, cls=None, clone=None):
        clone = super(VariationPurchase, self).clone(cls=cls, clone=clone)
        clone.variation_key = self.variation_key
        return clone

    class Meta:
        abstract = True
        verbose_name = _("variation purchase")
        verbose_name_plural = _("variation purchases")


@load(after='finalize_store_Purchase')
@load(action='finalize_variation_VariationPurchase')
def finalize_model():

    qs = modules.store.Purchase.objects.get_queryset()

    class VariationPurchaseQuerySet(qs.__class__):

        def mergeable_with(self, purchase):
            return super(VariationPurchaseQuerySet, self.filter(
                variation_key=purchase.variation_key)).mergeable_with(purchase)

    class VariationPurchaseManager(modules.store.Purchase.objects.__class__):

        def get_queryset(self):
            return VariationPurchaseQuerySet(self.model, using=self._db)

    class VariationPurchase(
            modules.variation.VariationPurchase,
            modules.store.Purchase):

        objects = VariationPurchaseManager()

        class Meta(
                modules.variation.VariationPurchase.Meta,
                modules.store.Purchase.Meta):
            app_label = 'store'

    modules.variation.VariationPurchase = VariationPurchase
    modules.variation.register(
        'VariationPurchaseQuerySet', VariationPurchaseQuerySet)
    modules.variation.register(
        'VariationPurchaseManager', VariationPurchaseManager)
