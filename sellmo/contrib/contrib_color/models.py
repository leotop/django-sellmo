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


from django.db import models
from django.db.models import Q
from django.db.models.query import QuerySet
from django.db.models.signals import pre_save, post_save, pre_delete
from django.utils.translation import ugettext_lazy as _
from django.contrib.contenttypes.models import ContentType

from sellmo import modules
from sellmo.api.decorators import load
from sellmo.contrib.contrib_attribute.query import value_q
from sellmo.contrib.contrib_attribute.adapters import AttributeTypeAdapter
from sellmo.magic import ModelMixin


class ColorAdapter(AttributeTypeAdapter):
    
    def get_choices(self):
        return modules.attribute.ValueObject.objects.all() \
            .filter(content_type__in=[
                ContentType.objects.get_for_model(modules.color.Color),
                ContentType.objects.get_for_model(modules.color.MultiColor)
            ]).polymorphic()
            
    def parse(self, string):
        try:
            return modules.color.Color.objects.get(name__iexact=string)
        except modules.color.Color.DoesNotExist:
            pass
        
        try:
            return modules.color.MultiColor.objects.get(name__iexact=string)
        except modules.color.MultiColor.DoesNotExist:
            pass
            
        raise ValueError()
    

class Color(models.Model):

    name = models.CharField(
        max_length=100,
        unique=True,
        verbose_name=_("name")
    )

    value = models.CharField(
        max_length=6,
        verbose_name=_("value")
    )

    def polymorphic_natural_key(self):
        return (self.name,)

    def __unicode__(self):
        return self.name

    class Meta:
        abstract = True
        ordering = ['name']
        verbose_name = _("color")
        verbose_name_plural = _("colors")


@load(action='finalize_color_Color')
@load(action='load_attribute_subtypes')
def finalize_model():
    class Color(modules.color.Color, modules.attribute.ValueObject):

        class Meta(modules.color.Color.Meta,
                   modules.attribute.ValueObject.Meta):
            app_label = 'attribute'

    modules.color.Color = Color


@load(after='finalize_color_Color')
def load_manager():

    class ColorManager(modules.color.Color.objects.__class__):

        def get_by_polymorphic_natural_key(self, name):
            return self.get(name=name)

    class Color(ModelMixin):
        model = modules.color.Color
        objects = ColorManager()


class MultiColor(models.Model):

    name = models.CharField(
        max_length=100,
        unique=True,
        verbose_name=_("name")
    )
    
    colors = models.ManyToManyField(
        'attribute.Color',
        verbose_name=_("colors")
    )

    def polymorphic_natural_key(self):
        return (self.name,)

    def __unicode__(self):
        return self.name

    class Meta:
        abstract = True
        ordering = ['name']
        verbose_name = _("multicolor")
        verbose_name_plural = _("multicolors")


@load(action='finalize_color_MultiColor')
@load(after='finalize_attribute_ValueObject')
def finalize_model():
    class MultiColor(modules.color.MultiColor, modules.attribute.ValueObject):

        class Meta(modules.color.MultiColor.Meta,
                   modules.attribute.ValueObject.Meta):
            app_label = 'attribute'

    modules.color.MultiColor = MultiColor
    

@load(before='finalize_attribute_Attribute')
def register_attribute_types():
    modules.attribute.register_attribute_type(
        'color',
        ColorAdapter(),
        verbose_name=_("color"))


@load(after='finalize_color_MultiColor')
def load_manager():

    class MultiColorManager(modules.color.MultiColor.objects.__class__):

        def get_by_polymorphic_natural_key(self, name):
            return self.get(name=name)

    class MultiColor(ModelMixin):
        model = modules.color.MultiColor
        objects = MultiColorManager()


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
                exists = modules.attribute.Value.objects \
                                .for_product_or_variants_of(product)
            else:
                exists = modules.attribute.Value.objects.for_product(product)

            exists = exists.filter(value_q(value.attribute, value.value))
            if ignore_value:
                exists = exists.exclude(pk=value.pk)
            exists = exists.count() > 0

            kwargs = {
                'color': color,
                'product': product,
                'attribute': value.attribute,
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
    
    color = models.ForeignKey(
        'attribute.Color',
        db_index=True,
        editable=False,
        related_name='+'
    )
    
    product = models.ForeignKey(
        'product.Product',
        db_index=True,
        editable=False,
        related_name='+',
    )
    
    attribute = models.ForeignKey(
        'attribute.Attribute',
        db_index=True,
        editable=False,
        related_name='+',
    )

    def __unicode__(self):
        return (
            u"{0} - {1} : {2}"
            .format(self.product, self.attribute, self.color))

    class Meta:
        unique_together = ('product', 'attribute', 'color')
        verbose_name = _("color mapping")
        verbose_name_plural =_("color mappings")
        abstract = True


def on_value_pre_save(sender, instance, raw=False, update_fields=None,
                      **kwargs):
    if not raw and not instance.pk is None:
        value = modules.attribute.Value.objects.get(pk=instance.pk)
        modules.color.ColorMapping.objects.map_or_unmap(
            value, ignore_value=True)


def on_value_post_save(sender, instance, created, raw=False,
                       update_fields=None, **kwargs):
    if not raw:
        modules.color.ColorMapping.objects.map_or_unmap(instance)


def on_value_pre_delete(sender, instance, *args, **kwargs):
    modules.color.ColorMapping.objects.map_or_unmap(
        instance, ignore_value=True)


@load(after='finalize_attribute_Value')
def listen():
    pre_save.connect(on_value_pre_save, sender=modules.attribute.Value)
    post_save.connect(on_value_post_save, sender=modules.attribute.Value)
    pre_delete.connect(on_value_pre_delete, sender=modules.attribute.Value)


@load(action='finalize_color_ColorMapping')
def finalize_model():
    class ColorMapping(modules.color.ColorMapping):
        class Meta(modules.color.ColorMapping.Meta):
            app_label = 'color'

    modules.color.ColorMapping = ColorMapping


@load(before='finalize_product_Product')
def load_model():
    class Product(modules.product.Product):

        def get_colors(self, **kwargs):
            return modules.color.get_colors(product=self, **kwargs)

        colors = property(get_colors)

        class Meta(modules.product.Product.Meta):
            abstract = True

    modules.product.Product = Product
