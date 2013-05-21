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
from sellmo.magic import ModelMixin
from sellmo.utils.polymorphism import PolymorphicModel, PolymorphicManager
from sellmo.contrib.contrib_variation.variant import VariantFieldDescriptor, VariantMixin
from sellmo.contrib.contrib_variation.utils import generate_slug

#

from django.db import models
from django.db.models import Q, F, Count
from django.db.models.query import QuerySet
from django.db.models.signals import pre_save, post_save, pre_delete
from django.core.exceptions import ValidationError
from django.utils.translation import ugettext_lazy as _

#
                
@load(after='load_variants')
def load_model():
    for subtype in modules.variation.product_subtypes:
        class ProductMixin(ModelMixin):
            model = subtype
            
            @property
            def variations(self):
                return self.get_variations()
            
            def get_variations(self, grouped=False, **kwargs):
                return modules.variation.get_variations(product=self, grouped=grouped, **kwargs)
                
@load(action='load_variants', after='setup_variants')
def load_variants():
    for subtype in modules.variation.product_subtypes:
        class Meta:
            app_label = 'product'
            verbose_name = _("variant")
            verbose_name_plural = _("variants")
    
        name = '%sVariant' % subtype.__name__
        attr_dict = {
            'product' : models.ForeignKey(
                subtype,
                related_name = 'variants',
                editable = False
            ),
            'Meta' : Meta,
            '__module__' : subtype.__module__
        }
        
        model = type(name, (VariantMixin, subtype,), attr_dict)
        for field in model.get_variable_fields():
            descriptor = field.model.__dict__.get(field.name, None)
            setattr(model, field.name, VariantFieldDescriptor(field, descriptor=descriptor))
        
        modules.variation.subtypes.append(model)
        setattr(modules.variation, name, model)
                
def on_value_pre_save(sender, instance, *args, **kwargs):
    product = instance.product.downcast()
    instance.base_product = product
    if getattr(product, '_is_variant', False):
        instance.base_product = product.product
        
def on_value_post_save(sender, instance, created, update_fields=None, *args, **kwargs):
    if created or update_fields:
        modules.variation.Variation.objects.deprecate(instance.base_product)
    
def on_value_pre_delete(sender, instance, *args, **kwargs):
    modules.variation.Variation.objects.deprecate(instance.base_product)
        
@load(after='finalize_attribute_Value')
def listen():
    pre_save.connect(on_value_pre_save, sender=modules.attribute.Value)
    post_save.connect(on_value_post_save, sender=modules.attribute.Value)
    pre_delete.connect(on_value_pre_delete, sender=modules.attribute.Value)
    

@load(after='finalize_attribute_Attribute') 
def load_manager():

    qs = modules.attribute.Attribute.objects.get_query_set()
    
    class AttributeQuerySet(qs.__class__):
        def for_product(self, product):
            return self.filter(Q(values__product=product) | Q(values__base_product=product)).distinct()
    
    class AttributeManager(modules.attribute.Attribute.objects.__class__):
        def get_query_set(self):
            return AttributeQuerySet(self.model)
    
    class Attribute(ModelMixin):
        model = modules.attribute.Attribute
        objects = AttributeManager()
    
    
@load(before='finalize_attribute_Attribute')
def load_model():

    class Attribute(modules.attribute.Attribute):
        
        variates = models.BooleanField(
            
        )
        
        groups = models.BooleanField(
            
        )
        
        class Meta:
            abstract = True
        
    modules.attribute.Attribute = Attribute
    
@load(after='finalize_attribute_Value') 
def load_manager():
    
    qs = modules.attribute.Value.objects.get_query_set()
    
    class ValueQuerySet(qs.__class__):
        def recipe(self, exclude=False):
            if exclude:
                return self.filter(recipe=None)
            return self
            
        def for_product(self, product):
            return self.filter(~Q(base_product=F('product')) | Q(recipe__isnull=False), base_product=product)
            
        def for_attribute(self, attribute, distinct=False):
            q = self.filter(attribute=attribute)
            if distinct:
                values = q.values_list(attribute.value_field, flat=True).distinct()
                distinct = []
                for value in values:
                    qargs = {
                        attribute.value_field : value
                    }
                    id = q.filter(**qargs).annotate(has_recipe=Count('recipe')).order_by('-has_recipe')[0].id
                    distinct.append(id)
                return q.filter(id__in=distinct)
            else:
                return q
    
    class ValueManager(modules.attribute.Value.objects.__class__):
        
        def __init__(self, *args, **kwargs):
            self.recipeless = False
            if kwargs.has_key('recipeless'):
                self.recipeless = kwargs.pop('recipeless')
            super(ValueManager, self).__init__(*args, **kwargs)
    
        def get_query_set(self):
            return ValueQuerySet(self.model).recipe(exclude=self.recipeless)
            
        def recipe(self, *args, **kwargs):
            return ValueQuerySet(self.model).recipe(*args, **kwargs)
            
    class Value(ModelMixin):
        model = modules.attribute.Value
        objects = ValueManager(recipeless=True)

@load(before='finalize_attribute_Value')
@load(after='finalize_variation_VariationRecipe')
def load_model():
    
    class Value(modules.attribute.Value):
        
        # The attribute to which we belong
        recipe = models.ForeignKey(
            modules.variation.VariationRecipe,
            db_index = True,
            null = True,
            blank = True,
            editable = False,
            related_name = 'values'
        )
        
        #
        base_product = models.ForeignKey(
            modules.product.Product,
            db_index = True,
            null = True,
            blank = True,
            editable = False,
            related_name = '+',
        )
        
        class Meta:
            abstract = True
        
    modules.attribute.Value = Value
    
@load(action='finalize_variation_VariationRecipe')
@load(after='finalize_product_Product')
def finalize_model():
    
    class VariationRecipe(modules.variation.VariationRecipe):
        
        # The product to which we apply
        product = models.OneToOneField(
            modules.product.Product,
            db_index = True,
            related_name = 'recipe',
        )
        
    modules.variation.VariationRecipe = VariationRecipe
        
    
class VariationRecipe(models.Model):

    def __unicode__(self):
        return unicode(self.product)

    class Meta:
        app_label = 'variation'
        abstract = True
        verbose_name = _("variation recipe")
        verbose_name_plural = _("variation recipes")
        
@load(action='finalize_variation_Variation')
@load(after='finalize_attribute_Value')
@load(after='finalize_product_Product')
def finalize_model():
    
    class Variation(modules.variation.Variation):
                
        # The product we are based on
        product = models.ForeignKey(
            modules.product.Product,
            db_index = True,
            editable = False,
            related_name = '+',
        )
        
        # The variant we are based on (can be a product)
        variant = models.ForeignKey(
            modules.product.Product,
            db_index = True,
            editable = False,
            related_name = '+',
        )
        
        #
        values = models.ManyToManyField(
            modules.attribute.Value,
            editable = False,
            related_name = '+',
        )
                
    modules.variation.Variation = Variation
    
class VariationManager(models.Manager):
    
    def build(self, product):
        
        # Delete any existing variations (always)
        existing = self.filter(product=product)
        existing.delete()
        
        # Get all attributes related to this product
        attributes = modules.attribute.Attribute.objects.for_product(product)
        
        # No attributes, means no variations
        if not attributes:
            return
            
        invalidations = []
        def _construct(variation_values):
            
            variant = None
            
            # Try to invaldiate values
            for value in variation_values:
                if value in invalidations:
                    return None
            
            # Find variant (if any)
            for value in variation_values:
                if value.recipe is None:
                    variant = value.product
                    break
                
            # 
            if variant is None:
                variant = product
            else:
                # Constructing explicit variation
                # Find all explicit values
                # And see if we're dealing with a 'fully' explicit variation
                # A fully explicit variation should exclude it's values
                fully_explicit=True
                for value in list(variation_values):
                    try:
                        explicit = modules.attribute.Value.objects.get(product=variant, attribute=value.attribute)
                    except modules.attribute.Value.DoesNotExist:
                        fully_explicit=False
                    else:
                        variation_values[variation_values.index(value)] = explicit
                        
                if fully_explicit:
                    invalidations.extend(variation_values)
                        
            
            variation = modules.variation.Variation.objects.create(
                id = modules.variation.Variation.generate_id(product, variation_values),
                product = product,
                variant = variant,
            )
            
            variation.values.add(*variation_values)
        
        def _variate(attribute_queue, variation_values=[]):
            variations = []
            if not attribute_queue:
                # Create the variation
                variation = _construct(variation_values)
                if not variation is None:
                    variations.append(variation)
            else:
                attribute = attribute_queue[0]
                for value in modules.attribute.Value.objects.recipe().for_attribute(attribute=attribute, distinct=True):
                    variations.extend(_variate(attribute_queue[1:], variation_values + [value]))
                
            return variations
            
        variations = _variate(attributes)
        return variations
    
    def deprecate(self, product):
        self.select_for_update().filter(product=product).update(deprecated=True)
        
    def for_product(self, product):
        variations = self.filter(product=product, deprecated=False)
        if variations.count() > 0:
            return variations
        else:
            self.build(product)
        return self.filter(product=product)
            
        
class Variation(models.Model):

    objects = VariationManager()
    
    @staticmethod
    def generate_id(product, values):
        return generate_slug(product=product, values=values, full=True, unique=False)

    id = models.CharField(
        max_length = 255,
        primary_key = True,
        editable = False,
    )
        
    # Flags
    deprecated = models.BooleanField(
        editable = False,
    )
    
    def __unicode__(self):
        return self.id

    class Meta:
        app_label = 'variation'
        abstract = True
        verbose_name = _("variation")
        verbose_name_plural = _("variations")
        ordering = ['id']
    
@load(after='finalize_store_Purchase')
def load_model():
    
    class VariationPurchase(modules.store.Purchase):
        
        variation_key = models.CharField(
            max_length = 255
        )
        
        # Auto generated description, usefull when variation is unavailable
        variation_description = models.CharField(
            max_length = 255
        )
        
        def describe(self):
            return self.variation_name
        
        class Meta:
            app_label = 'store'
        
    modules.variation.VariationPurchase = VariationPurchase
        
# Init modules
from sellmo.contrib.contrib_variation.modules import *