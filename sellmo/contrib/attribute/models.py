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
from django.db.models.query import QuerySet, ValuesQuerySet
from django.utils import six
from django.utils.translation import ugettext_lazy as _

from sellmo import modules
from sellmo.magic import ModelMixin
from sellmo.api.decorators import load
from sellmo.core.query import PKIterator
from sellmo.utils.formatting import call_or_format
from sellmo.contrib.attribute.fields import (AttributeKeyField, 
                                             AttributeTypeField)
from sellmo.contrib.attribute.helpers import AttributeHelper

    

@load(before='finalize_product_Product')
def load_model():
    class Product(modules.product.Product):

        def __init__(self, *args, **kwargs):
            super(Product, self).__init__(*args, **kwargs)
            self.attributes = AttributeHelper(self)

        def save(self, *args, **kwargs):
            super(Product, self).save(*args, **kwargs)
            self.attributes.save()

        class Meta(modules.product.Product.Meta):
            abstract = True

    modules.product.Product = Product
    

@load(after='finalize_attribute_Attribute')
@load(before='finalize_attribute_Value')
def load_model():
    
    Value = modules.attribute.Value
    
    value_fields = [
        typ.get_value_field_name()
        for typ in six.itervalues(modules.attribute.attribute_types)]
    
    class Meta(Value.Meta):
        abstract = True
        ordering = ['attribute'] + value_fields

    
    attr_dict = {
        'Meta': Meta,
        '__module__': Value.__module__
    }
    
    for typ in six.itervalues(modules.attribute.attribute_types):
        attr_dict[typ.get_value_field_name()] = typ.get_value_field()
    
    Value = type('Value', (Value,), attr_dict)
    modules.attribute.Value = Value


@load(action='finalize_attribute_Value')
def finalize_model():
    class Value(modules.attribute.Value):
        class Meta(modules.attribute.Value.Meta):
            app_label = 'attribute'

    modules.attribute.Value = Value


class SmartValueValuesQuerySet(ValuesQuerySet):
    
    def iterator(self):
        rows = []
        
        last_col = None
        def get_used_value_type(row):
            if last_col:
                typ = value_types.get(last_col, None)
                if typ and not typ.is_empty(row[last_col]):
                    return typ
            for col in row:
                typ = value_types.get(col, None)
                if typ and not typ.is_empty(row[col]):
                    # Keep track of last col to speed
                    # up large querysets
                    last_col = col
                    return typ
            return None
        
        value_types = {
            typ.get_value_field_name(): typ
            for typ in six.itervalues(modules.attribute.attribute_types)
        }
        
        # Keeps track of pk's for each model to prefetch
        value_models = {
            typ.get_model(): set()
            for typ in six.itervalues(modules.attribute.attribute_types)
            if typ.get_model()
        }
        
        # Keeps track of pk's for attribute to prefetch     
        attributes = set()
        
        for row in super(SmartValueValuesQuerySet, self).iterator():
            if 'attribute' in row:
                attributes.add(row['attribute'])
            
            typ = get_used_value_type(row)
            if typ:
                value = row[typ.get_value_field_name()]
                row['value'] = value
                model = typ.get_model()
                if model:
                    value_models[model].add(value)
                
            rows.append(row)
            
        # Lookup Attributes
        attributes = ({
            obj.pk: obj for obj in PKIterator(
                modules.attribute.Attribute,
                attributes)}
            if attributes else {})
                    
        # Lookup value models
        value_models = {
            model: ({
                obj.pk: obj for obj in PKIterator(model, pks)
            } if pks else {})
            for model, pks in six.iteritems(value_models)}
        
        for row in rows:
            if 'attribute' in row:
                row['attribute'] = attributes[row['attribute']]
            typ = get_used_value_type(row)
            if typ:
                model = typ.get_model()
                if model:
                    row['value'] = value_models[model][row['value']]
            yield row
    

class ValueQuerySet(QuerySet):

    def for_product(self, product):
        return self.filter(product=product)

    def for_attribute(self, attribute):
        return self.filter(attribute=attribute)
        
    def smart_values(self, *fields):
        fields = list(fields)
        value_field_names = [
            typ.get_value_field_name()
            for typ in six.itervalues(modules.attribute.attribute_types)
        ]
        
        if 'value' in fields:
            fields.remove('value')
            fields.extend(value_field_names)
        
        values = self.values(*fields)
        values = values._clone(klass=SmartValueValuesQuerySet)
        return values
    

class ValueManager(models.Manager):

    def get_by_natural_key(self, attribute, product):
        return self.get(
            attribute=modules.attribute.Attribute.get_by_natural_key(
                *attribute),
            product=modules.product.Product.get_by_natural_key(*product)
        )

    def get_queryset(self):
        return ValueQuerySet(self.model, using=self._db)

    def for_product(self, *args, **kwargs):
        return self.get_queryset().for_product(*args, **kwargs)

    def for_attribute(self, *args, **kwargs):
        return self.get_queryset().for_attribute(*args, **kwargs)


class Value(models.Model):

    objects = ValueManager()
    
    # E(A)V
    attribute = models.ForeignKey(
        'attribute.Attribute',
        db_index=True,
        verbose_name=_(u"attribute"),
        related_name='values',
        on_delete=models.PROTECT
    )
    
    # (E)AV
    product = models.ForeignKey(
        'product.Product',
        db_index=True,
        related_name='values',
    )

    def get_value(self):
        field_name = self.attribute.get_type().get_value_field_name()
        value = getattr(self, field_name)
        return value

    def set_value(self, value):
        if value != self.get_value():
            self._old_value = self.get_value()
        field_name = self.attribute.get_type().get_value_field_name()
        setattr(self, field_name, value)

    value = property(get_value, set_value)

    _old_value = None

    def get_old_value(self):
        if self._old_value is None:
            return self.get_value()
        return self._old_value

    old_value = property(get_old_value)
    
    def is_empty(self):
        return self.attribute.get_type().is_empty(self.get_value())

    def save_value(self):
        # Re-assign product
        self.product = self.product
        if not self.is_empty():
            self.save()
        elif not self.pk is None:
            self.delete()

    def natural_key(self):
        return (self.attribute.natural_key(), self.product.natural_key())
    natural_key.dependencies = ['attribute.attribute', 'product.product']

    def __unicode__(self):
        # Do not simply supply value=self, this would encourage recursive calls to
        # __unicode__
        return call_or_format(modules.attribute.value_format, value=self.value, attribute=self.attribute)

    class Meta:
        abstract = True
        verbose_name = _("value")
        verbose_name_plural = _("values")
    

@load(action='finalize_attribute_Attribute')
def finalize_model():

    choices = []
    for typ in six.itervalues(modules.attribute.attribute_types):
        choices.append((typ.key, typ.get_verbose_name()))

    class Attribute(modules.attribute.Attribute):
        
        type = AttributeTypeField(
            max_length=255,
            db_index=True,
            choices=choices,
            default=choices[0][0] if choices else None
        )
        
        class Meta(modules.attribute.Attribute.Meta):
            app_label = 'attribute'

    modules.attribute.Attribute = Attribute


class AttributeQuerySet(QuerySet):

    def for_product(self, product):
        return self.filter(values__product=product).distinct()


class AttributeManager(models.Manager):

    def get_by_natural_key(self, key):
        return self.get(key=key)

    def get_queryset(self):
        return AttributeQuerySet(self.model, using=self._db)

    def for_product(self, *args, **kwargs):
        return self.get_queryset().for_product(*args, **kwargs)


class Attribute(models.Model):

    objects = AttributeManager()

    name = models.CharField(
        max_length=100
    )

    key = AttributeKeyField(
        max_length=50,
        db_index=True,
        blank=True
    )

    required = models.BooleanField(
        default=False
    )

    visible = models.BooleanField(
        default=True
    )

    sort_order = models.SmallIntegerField(
        default=0,
        verbose_name=_("sort order"),
    )

    def save(self, *args, **kwargs):
        old = None
        
        if self.pk:
            old = modules.attribute.Attribute.objects.get(pk=self.pk)
        elif not self.key:
            self.key = AttributeKeyField.create_key_from_name(self.name)

        if old is not None and old.values.count() > 0:
            if self.type != old.type:
                raise Exception((_("Cannot change attribute type "
                                   "of an attribute that is already "
                                   " in use.")))

        super(Attribute, self).save(*args, **kwargs)

    def parse(self, string):
        return self.get_type().parse(string)
        
    def get_type(self):
        return modules.attribute.attribute_types[self.type]

    def natural_key(self):
        return (self.key,)

    def __unicode__(self):
        return self.name

    class Meta:
        abstract = True
        ordering = ['sort_order', 'name']
        verbose_name = _("attribute")
        verbose_name_plural = _("attributes")
        
        
@load(after='finalize_product_Product')
def load_manager():

    qs = modules.product.Product.objects.get_queryset()

    class ProductQuerySet(qs.__class__):
        
        _prefetch_attributes = None
        _prefetched_attributes = None
        _prefetched_values = None
        
        def __iter__(self):
            out = []
            for obj in super(ProductQuerySet, self).__iter__():
                out.append(obj)
            
            if self._prefetch_attributes is not None:
                if self._prefetched_attributes is None:
                    self._prefetched_attributes = self \
                        ._get_prefetched_attributes()
                if self._prefetched_values is None:
                    self._prefetched_values = self \
                        ._get_prefetched_values()
                        
                # Map values to product
                product_to_values = {}
                for value in self._prefetched_values:
                    if value.product.pk not in product_to_values:
                        product_to_values[value.product.pk] = []
                    product_to_values[value.product.pk].append(value)
                    
                for obj in out:
                    # Populate with mapped values and global attributes
                    obj.attributes.populate(
                        product_to_values.get(obj.pk, []),
                        self._prefetched_attributes)
                
            for obj in out:
                yield obj
        
        def _clone(self, *args, **kwargs):
            clone = super(ProductQuerySet, self)._clone(*args, **kwargs)
            if self._prefetch_attributes is not None:
                clone._prefetch_attributes = list(self._prefetch_attributes)
            return clone
            
        def _get_prefetched_values(self):
            prefetched = modules.attribute \
                .Value.objects.filter(product__in=self) \
                .select_related('product__id', 'attribute')
            if len(self._prefetch_attributes) > 0:
                prefetched = prefetched.filter(
                    attribute__key__in=self._prefetch_attributes)
            return prefetched
            
        def _get_prefetched_attributes(self):
            prefetched = modules.attribute.Attribute.objects.all()
            if len(self._prefetch_attributes) > 0:
                prefetched = prefetched.filter(
                    key__in=self._prefetch_attributes)
            return prefetched
        
        def prefetch_attributes(self, *attributes):
            clone = self._clone()
            clone._prefetch_attributes = list(attributes)
            return clone

    class ProductManager(modules.product.Product.objects.__class__):
        
        def get_queryset(self):
            return ProductQuerySet(self.model, using=self._db)

    class Product(ModelMixin):
        model = modules.product.Product
        objects = ProductManager()

    # Register
    modules.product.ProductQuerySet = ProductQuerySet
    modules.product.ProductManager = ProductManager
