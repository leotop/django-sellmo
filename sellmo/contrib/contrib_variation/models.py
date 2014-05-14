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
from sellmo.magic import ModelMixin
from sellmo.utils.formatting import call_or_format
from sellmo.core.polymorphism import PolymorphicModel, PolymorphicManager
from sellmo.contrib.contrib_variation.variant import (VariantFieldDescriptor,
                                                      VariantMixin,
                                                      get_differs_field_name)
from sellmo.contrib.contrib_variation.utils import generate_slug
from sellmo.contrib.contrib_variation.signals import (variations_deprecating,
                                                      variations_invalidated)
from sellmo.contrib.contrib_variation.helpers import (AttributeHelper,
                                                      VariantAttributeHelper,
                                                      VariationAttributeHelper)
from sellmo.contrib.contrib_attribute.query import ProductQ

from django.db import models, transaction, IntegrityError
from django.db.models import Q, F, Count
from django.db.models.query import QuerySet
from django.db.models.signals import pre_save, post_save, pre_delete
from django.core.exceptions import ValidationError
from django.contrib.contenttypes.models import ContentType
from django.utils.translation import ugettext_lazy as _

import sys
import logging


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

    qs = modules.product.Product.objects.get_query_set()

    class ProductQuerySet(qs.__class__):

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

        def get_query_set(self):
            return ProductQuerySet(self.model)

        def variants(self, *args, **kwargs):
            return self.get_query_set().variants(*args, **kwargs)

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

            @property
            def grouped_by(self):
                try:
                    return modules.attribute.Attribute.objects \
                                  .which_variate(self).get(groups=True)
                except modules.attribute.Attribute.DoesNotExist:
                    return None

            @property
            def grouped_choices(self):
                group = self.grouped_by
                if group:
                    return modules.attribute.Value.objects \
                                  .which_variate(self) \
                                  .for_attribute(group, distinct=True)
                else:
                    return None

            @property
            def variated_by(self):
                return modules.attribute.Attribute.objects.which_variate(self)

            def get_variations(self, invalidated=False):
                if getattr(self, '_is_variant', False):
                    return modules.variation.Variation.objects \
                                  .for_product(
                                    self.product, invalidated=invalidated) \
                                  .filter(variant=self)
                return modules.variation.Variation.objects \
                              .for_product(self, invalidated=invalidated)

            @property
            def variations(self):
                return self.get_variations()


@load(action='load_variants')
@load(after='setup_variants')
@load(after='finalize_variation_Variant')
def load_variants():
    for subtype in modules.variation.product_subtypes:
        class Meta(subtype.Meta):
            app_label = 'product'
            verbose_name = _("variant")
            verbose_name_plural = _("variants")

        name = '%sVariant' % subtype.__name__
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

    qs = modules.attribute.Attribute.objects.get_query_set()

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

        def get_query_set(self):
            return AttributeQuerySet(self.model)

        def for_product_or_variants_of(self, *args, **kwargs):
            return self.get_query_set() \
                       .for_product_or_variants_of(*args, **kwargs)

        def which_variate(self, *args, **kwargs):
            return self.get_query_set().which_variate(*args, **kwargs)

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
                for product in modules.product.Product.objects.filter(
                        ProductQ(attribute=self,
                                 product_field='base_product')):
                    modules.variation.Variation.objects.invalidate(product)

        class Meta(modules.attribute.Attribute.Meta):
            abstract = True

    modules.attribute.Attribute = Attribute


@load(after='finalize_attribute_Value')
def load_manager():

    qs = modules.attribute.Value.objects.get_query_set()

    class ValueQuerySet(qs.__class__):

        def for_product_or_variants_of(self, product):
            q = Q(product=product) | Q(base_product=product)
            return self.filter(q)

        def for_attribute(self, attribute, distinct=False):
            q = self.filter(attribute=attribute)
            if distinct:
                values = q.values_list(
                    attribute.value_field, flat=True).distinct()
                distinct = []
                for value in values:
                    qargs = {
                        attribute.value_field: value
                    }
                    id = q.filter(**qargs) \
                          .annotate(does_variate=Count('variates')) \
                          .order_by('-does_variate')[0].id
                    distinct.append(id)
                return q.filter(id__in=distinct)
            else:
                return q

        def which_variate(self, product):
            return self.filter(
                Q(attribute__variates=True) &
                (Q(base_product=product) |
                 Q(product=product) & 
                 Q(variates=True)))

    class ValueManager(modules.attribute.Value.objects.__class__):

        def get_query_set(self):
            return ValueQuerySet(self.model)

        def for_product_or_variants_of(self, *args, **kwargs):
            return self.get_query_set() \
                       .for_product_or_variants_of(*args, **kwargs)

        def which_variate(self, *args, **kwargs):
            return self.get_query_set().which_variate(*args, **kwargs)

    class Value(ModelMixin):
        model = modules.attribute.Value
        objects = ValueManager()

    modules.attribute.register('ValueQuerySet', ValueQuerySet)
    modules.attribute.register('ValueManager', ValueManager)


@load(before='finalize_attribute_Value')
@load(after='finalize_product_Product')
@load(after='finalize_variation_VariationRule')
def load_model():

    class Value(modules.attribute.Value):

        base_product = models.ForeignKey(
            modules.product.Product,
            db_index=True,
            null=True,
            blank=True,
            editable=False,
            related_name='+'
        )

        variates = models.BooleanField(
            default=False,
            editable=False
        )

        class Meta(modules.attribute.Value.Meta):
            abstract = True

    modules.attribute.Value = Value


@load(action='finalize_variation_Variation')
@load(after='finalize_attribute_Value')
@load(after='finalize_product_Product')
def finalize_model():

    class Variation(modules.variation.Variation):

        # The product we are based on
        product = models.ForeignKey(
            modules.product.Product,
            db_index=True,
            editable=False,
            related_name='+',
            verbose_name=_("product"),
        )

        # The variant we are based on (can be product)
        variant = models.ForeignKey(
            modules.product.Product,
            db_index=True,
            editable=False,
            related_name='+',
            verbose_name=_("variant"),
        )

        # The variant we are based on and which is common across every
        # variation in the group (can be a product)
        group_variant = models.ForeignKey(
            modules.product.Product,
            db_index=True,
            editable=False,
            null=True,
            related_name='+',
            verbose_name=_("group variant"),
        )

        #
        values = models.ManyToManyField(
            modules.attribute.Value,
            editable=False,
            related_name='+',
            verbose_name=_("values"),
        )

        class Meta(modules.variation.Variation.Meta):
            app_label = 'variation'
            ordering = ['sort_order']
            verbose_name = _("variation")
            verbose_name_plural = _("variations")

    modules.variation.Variation = Variation


class VariationQuerySet(QuerySet):

    def for_product(self, product):
        return self.filter(product=product)


class VariationManager(models.Manager):

    @transaction.atomic
    def build(self, product):

        product = product.downcast()

        # Delete any existing variations (always)
        existing = self.filter(product=product)
        existing.delete()

        # Get all attributes related to this product
        attributes = modules.attribute.Attribute.objects.which_variate(product)
        if attributes.count() == 0:
            return

        # Do we have an attribute which groups ?
        group = attributes.filter(groups=True).first()

        # CONVERT TO LIST FOR PERFORMANCE AND INDEXING
        attributes = list(attributes)

        # Keep track of explicit attributes
        explicits = {}
        for attribute in attributes:
            for value in modules.attribute.Value.objects \
                                .which_variate(product) \
                                .for_attribute(attribute, distinct=True):
                if value.variates:
                    explicits[attribute.key] = False
                    break
            else:
                explicits[attribute.key] = True

        # Create all possible variations
        combinations = []
        
        def _combine(attributes, combination):
            if attributes:
                attribute = attributes[0]
                values = modules.attribute.Value.objects.which_variate(
                    product).for_attribute(attribute, distinct=True)
                for value in modules.attribute.get_sorted_values(
                        values=values, attribute=attribute):
                    _combine(attributes[1:], combination + [value])
            else:
                for value in list(combination):
                    index = combination.index(value)
                    if not value.variates:
                        combination[index] = value.get_value()
                combinations.append(combination)
        
        _combine(attributes, [])
        
        # Mix in variants
        for variant in product.variants.all():
            # Find values related to this variant
            values = modules.attribute.Value.objects.for_product(
                variant).filter(attribute__in=attributes)
        
            for combination in combinations:
                for value in values:
                    index = attributes.index(value.attribute)
                    current = combination[index]
                    if isinstance(current, modules.attribute.Value):
                        current = current.get_value()
                    if current != value.get_value():
                        break
                else:
                    # Override with variant values
                    for value in values:
                        index = attributes.index(value.attribute)
                        combination[index] = value
        
        # Fix non existent explicit combinations
        for attribute in attributes:
            if explicits[attribute.key]:
                index = attributes.index(attribute)
                for combination in combinations:
                    value = combination[index]
                    if not isinstance(value, modules.attribute.Value):
                        combination[index] = None
        
        # Filter out non existent combinations
        for combination in list(combinations):
            for value in combination:
                if (value is not None and 
                        not isinstance(value, modules.attribute.Value)):
                    index = combinations.index(combination)
                    combinations.pop(index)
                    break
        
        # Filter out duplicate combinations
        existing = []
        for combination in list(combinations):
            signature = [
                value.get_value() for value in combination if 
                not value is None]
            if signature in existing:
                index = combinations.index(combination)
                combinations.pop(index)
            existing.append(signature)
        
        # Create variations
        sort_order = 0
        while combinations:
            combination = combinations.pop(0)
            values = [value for value in combination if not value is None]
        
            # Skip empties
            if not values:
                continue
            
            # Find variant
            variant = product
            # Will match a variant who matches all this combination's values
            exact = Q()
            # Will match a variant who matches all this combination's values
            # except the group
            best = Q()
            for value in values:
                if getattr(value.product.downcast(), '_is_variant', False):
                    exact &= ProductQ(value.attribute, value.get_value())
                    if value.attribute != group:
                        best &= ProductQ(value.attribute, value.get_value())
                    else:
                        best &= ~ProductQ(value.attribute)
                else:
                    exact &= ~ProductQ(value.attribute)
                    best &= ~ProductQ(value.attribute)

            # Try to find exact match
            for q in (exact, best):
                if q:
                    try:
                        variant = product.variants.get(q)
                    except (modules.product.Product.DoesNotExist, 
                            modules.product.Product.MultipleObjectsReturned):
                        continue
                    else:
                        break
        
            # Collect non explicit values
            non_explicit_values = [
                value for value in values if value.variates
            ]
        
            variation = modules.variation.Variation.objects.create(
                id=generate_slug(
                    product=variant, values=values, full=True, 
                    unique=False),
                description=modules.variation.generate_variation_description(
                    prefix=unicode(variant), values=non_explicit_values),
                product=product,
                variant=variant,
                sort_order=sort_order
            )

            variation.values.add(*values)
            sort_order += 1

        # Handle grouping
        if group:
            # We need to find a single variant which is common across all
            # variations in this group
            for value in modules.attribute.Value.objects \
                                .which_variate(product) \
                                .for_attribute(attribute=group, distinct=True):
                # Get variations for this grouped attribute / value combination
                qargs = {
                    'values__attribute': group,
                    'values__%s' % group.value_field: value.get_value(),
                }
                variations = modules.variation.Variation.objects.filter(
                    product=product).filter(**qargs)

                # Get variant
                qargs = [ProductQ(group, value.get_value())]
                if variations.count() > 1:
                    # Get single variant common across all variations
                    for attribute in attributes:
                        if attribute != group:
                            q = ~ProductQ(attribute)
                            qargs.append(q)
                try:
                    variant = product.variants.get(*qargs)
                except modules.product.Product.DoesNotExist:
                    variant = product
                except modules.product.Product.MultipleObjectsReturned:
                    logger.warning(
                        "Invalid variant consruction in combination "
                        "with grouping")
                    logger.info(product.variants.filter(*qargs))

                variations.update(group_variant=variant)

        # Finally update product
        product.variations_invalidated = False

    def invalidate(self, product):
        if not product.variations_invalidated:
            variations_deprecating.send(self, product=product)
            product.variations_invalidated = True
            variations_invalidated.send(self, product=product)

    def get_query_set(self):
        return VariationQuerySet(self.model)

    def for_product(self, product, invalidated=False):
        product = product.downcast()

        # Capture IntegrityError's as these are caused by concurrency.
        # Output will always be valid due to transactions.
        def build():
            try:
                self.build(product)
            except IntegrityError as ex:
                pass

        if not invalidated and product.variations_invalidated:
            # Variations invalidated, rebuild
            build()
        build()
        # Get variations
        variations = self.get_query_set().for_product(product)

        if not invalidated and variations.count() == 0:
            # No variations, build
            build()
            variations = self.get_query_set().for_product(product)

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


@load(action='finalize_variation_VariationsState')
@load(after='finalize_product_Product')
def finalize_model():

    class VariationsState(modules.variation.VariationsState):

        product = models.OneToOneField(
            modules.product.Product,
            editable=False,
            related_name='variations_state'
        )

        class Meta(modules.variation.VariationsState.Meta):
            app_label = 'variation'
            verbose_name = _("variations state")
            verbose_name_plural = _("variations states")

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

        variations_invalidated = property(
            get_variations_invalidated, set_variations_invalidated)

        class Meta(modules.product.Product.Meta):
            abstract = True

    modules.product.Product = Product


class VariationsState(models.Model):

    invalidated = models.BooleanField(
        default=False,
        editable=False,
    )

    class Meta:
        abstract = True

    def __unicode__(self):
        return unicode(self.product)


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


@load(after='finalize_store_Purchase')
@load(action='finalize_variation_VariationPurchase')
def finalize_model():

    qs = modules.store.Purchase.objects.get_query_set()

    class VariationPurchaseQuerySet(qs.__class__):

        def mergeable_with(self, purchase):
            return super(VariationPurchaseQuerySet, self.filter(
                variation_key=purchase.variation_key)).mergeable_with(purchase)

    class VariationPurchaseManager(modules.store.Purchase.objects.__class__):

        def get_query_set(self):
            return VariationPurchaseQuerySet(self.model)

    class VariationPurchase(
            modules.variation.VariationPurchase,
            modules.store.Purchase):

        objects = VariationPurchaseManager()

        class Meta(
                modules.variation.VariationPurchase.Meta,
                modules.store.Purchase.Meta):
            app_label = 'store'
            verbose_name = _("variation purchase")
            verbose_name_plural = _("variation purchases")

    modules.variation.VariationPurchase = VariationPurchase
    modules.variation.register(
        'VariationPurchaseQuerySet', VariationPurchaseQuerySet)
    modules.variation.register(
        'VariationPurchaseManager', VariationPurchaseManager)
