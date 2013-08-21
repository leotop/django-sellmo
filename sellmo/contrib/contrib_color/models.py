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
from django.db.models.signals import pre_save, post_save, pre_delete

#

from sellmo import modules
from sellmo.api.decorators import load
from sellmo.contrib.contrib_attribute.models import ValueObject
from sellmo.contrib.contrib_attribute.query import ValueQ


#

class Color(ValueObject):
    
    name = models.CharField(max_length=100)
    value = models.CharField(max_length=6)
        
    def __unicode__(self):
        return self.name
        
    class Meta:
        app_label = 'attribute'
    
class MultiColor(ValueObject):
    
    name = models.CharField(max_length=100)
    colors = models.ManyToManyField(
        Color
    )
    
    def __unicode__(self):
        return self.name
    
    class Meta:
        app_label = 'attribute'
        
class ColorMappingQuerySet(QuerySet):
    
    def for_product(self, product):
        return self.filter(product=product)
        
    def for_attribute(self, attribute):
        return self.filter(attribute=attribute)
        
class ColorMappingManager(models.Manager):
    
    def get_query_set(self):
        return ColorMappingQuerySet(self.model)
        
    def for_product(self, *args, **kwargs):
        return self.get_query_set().for_product(*args, **kwargs)
        
    def for_attribute(self, *args, **kwargs):
        return self.get_query_set().for_attribute(*args, **kwargs)
    
    def map_or_unmap(self, value, ignore_value=False):
        color = value.value
        if color is None or not isinstance(color, (Color, MultiColor)):
            return
            
        colors = [color]
        if isinstance(color, MultiColor):
            colors = color.colors.all()
        
        product = value.product.downcast()
        products = [product]
        if getattr(product, '_is_variant', False):
            products.append(product.product)
            
        def do(product, color):
            if hasattr(modules, 'variation'):
                exists = modules.attribute.Value.objects.for_product_or_variant(product)
            else:
                exists = modules.attribute.Value.objects.for_product(product)
            
            exists = exists.filter(ValueQ(value.attribute, value.value))
            if ignore_value:
                exists = exists.exclude(pk=value.pk)
            exists = exists.count() > 0
            
            kwargs = {
                'color' : color,
                'product' : product,
                'attribute' : value.attribute,
            }
            
            if exists:
                # Ensure we have a mapping
                self.get_or_create(**kwargs)
            else:
                # Ensure no mapping is present
                self.filter(**kwargs).delete()
            
        for color in colors:
            for product in products:
                do(product, color)
            
        
class ColorMapping(models.Model):
    
    objects = ColorMappingManager()
    
    #
    
    color = models.ForeignKey(
        Color,
        db_index = True,
        editable = False
    )
    
    class Meta:
        abstract = True
        app_label = 'color'
        
#

def on_value_pre_save(sender, instance, update_fields=None, *args, **kwargs):
    if not instance.pk is None:
        value = modules.attribute.Value.objects.get(pk=instance.pk)
        modules.color.ColorMapping.objects.map_or_unmap(value, ignore_value=True)
        
def on_value_post_save(sender, instance, created, update_fields=None, *args, **kwargs):
    modules.color.ColorMapping.objects.map_or_unmap(instance)
        
def on_value_pre_delete(sender, instance, *args, **kwargs):
    modules.color.ColorMapping.objects.map_or_unmap(instance, ignore_value=True)

@load(after='finalize_attribute_Value')
def listen():
    pre_save.connect(on_value_pre_save, sender=modules.attribute.Value)
    post_save.connect(on_value_post_save, sender=modules.attribute.Value)
    pre_delete.connect(on_value_pre_delete, sender=modules.attribute.Value)
    
@load(action='finalize_color_ColorMapping')
@load(after='finalize_attribute_Attribute')
@load(after='finalize_product_Product')
def finalize_model():
    class ColorMapping(modules.color.ColorMapping):
        
        product = models.ForeignKey(
            modules.product.Product,
            db_index = True,
            editable = False,
            related_name = '+',
        )
        
        attribute = models.ForeignKey(
            modules.attribute.Attribute,
            db_index = True,
            editable = False,
            related_name = '+',
        )
        
        class Meta:
            unique_together = ('product', 'attribute', 'color')
            app_label = 'color'
            
    modules.color.ColorMapping = ColorMapping
         
@load(before='finalize_product_Product')
def load_model():
    class Product(modules.product.Product):

        def get_colors(self, attribute=None):
            colors = modules.color.ColorMapping.objects.for_product(self)
            if attribute:
                colors = colors.for_attribute(attribute)
            return modules.color.Color.objects.filter(pk__in=colors.values_list('color', flat=True))
            
        colors = property(get_colors)

        class Meta:
            abstract = True

    modules.product.Product = Product
        
# Init modules
from sellmo.contrib.contrib_color.modules import *