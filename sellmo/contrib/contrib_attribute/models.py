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
from django.utils.translation import ugettext_lazy as _

from sellmo import modules
from sellmo.magic import ModelMixin
from sellmo.api.decorators import load
from sellmo.core.polymorphism import PolymorphicModel, PolymorphicManager
from sellmo.utils.formatting import call_or_format
from sellmo.contrib.contrib_attribute.fields import (AttributeKeyField, 
                                                     AttributeTypeField)
from sellmo.contrib.contrib_attribute.helpers import AttributeHelper


VALUE_FIELDS = ['value_string', 'value_int', 'value_float', 'value_object']


class ValueObject(PolymorphicModel):
    class Meta:
        abstract = True
        verbose_name = _("value object")
        verbose_name_plural = _("value objects")


@load(action='finalize_attribute_ValueObject')
def finalize_model():
    
    class ValueObject(modules.attribute.ValueObject):
        class Meta(modules.attribute.ValueObject.Meta):
            app_label = 'attribute'

    modules.attribute.ValueObject = ValueObject
    

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


@load(action='finalize_attribute_Value')
def finalize_model():

    class Value(modules.attribute.Value):
        class Meta(modules.attribute.Value.Meta):
            app_label = 'attribute'

    modules.attribute.Value = Value


class AttributeValuesQuerySet(ValuesQuerySet):
    
    def __is_assigned__(self, row, field):
        value = row[field]
        if field == 'value_string':
            return value is not None and len(value) > 0
        return value is not None
    
    def iterator(self):
        last_field = None
        fields = []
        out = []
        for row in super(AttributeValuesQuerySet, self).iterator():
            # Try last used value field and yield
            if last_field and self.__is_assigned__(row, last_field):
                out.append((last_field, row[last_field]))
                continue
            
            # Find (new) used value field and yield
            for field in VALUE_FIELDS:
                if self.__is_assigned__(row, field):
                    # Keep track of this field
                    last_field = field
                    # Keep track of used fields
                    if field not in fields:
                        fields.append(field)
                    out.append((field, row[field]))
                    break
                    
        # Lookup ValueObjects
        value_objects = {}
        if 'value_object' in fields:
            for obj in (modules.attribute.ValueObject.objects
                    .polymorphic().filter(pk__in=self.values('value_object'))):
                value_objects[obj.pk] = obj
            
        for field, value in out:
            if field == 'value_object':
                yield value_objects[value]
            else:
                yield value
                
    

class ValueQuerySet(QuerySet):

    _prefetch_value_objects = False
    _prefetched_value_objects = None

    def for_product(self, product):
        return self.filter(product=product)

    def for_attribute(self, attribute):
        return self.filter(attribute=attribute)
        
    def attribute_values(self, attribute=None):
        values = self.values(*VALUE_FIELDS)
        return values._clone(klass=AttributeValuesQuerySet)
        
    def _clone(self, *args, **kwargs):
        clone = super(ValueQuerySet, self)._clone(*args, **kwargs)
        clone._prefetch_value_objects = self._prefetch_value_objects
        return clone
    
    def prefetch_value_objects(self):
        clone = self._clone()
        clone._prefetch_value_objects = True
        return clone
    
    def __iter__(self):
        out = []
        for obj in super(ValueQuerySet, self).__iter__():
            out.append(obj)
        
        if self._prefetch_value_objects:
            if self._prefetched_value_objects is None:
                self._prefetched_value_objects = modules.attribute \
                    .ValueObject.objects \
                    .polymorphic() \
                    .filter(values__in=self) \
                    .distinct()
                
            # Map value objects to pk
            value_objects = {}
            for value_object in self._prefetched_value_objects:
                value_objects[value_object.pk] = value_object
            
            # Assign value objects
            for value in out:
                if (value.value_object_id is not None and
                        value.value_object_id in value_objects):
                    value.value_object = value_objects[value.value_object_id]
            
        for obj in out:
            yield obj
    

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

    value_int = models.IntegerField(
        null=True,
        blank=True,
    )

    value_float = models.FloatField(
        null=True,
        blank=True,
    )

    value_string = models.CharField(
        max_length=255,
        blank=True,
        default='',
    )
    
    value_object = models.ForeignKey(
        'attribute.ValueObject',
        null=True,
        blank=True,
        db_index=True,
        on_delete=models.PROTECT,
        related_name='values'
    )
    
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
        field = self.attribute.value_field
        value = getattr(self, field)
        if field == 'value_object' and value:
            value = value.downcast()
        return value

    def set_value(self, value):
        if value != self.get_value():
            self._old_value = self.get_value()
        field = self.attribute.value_field
        setattr(self, field, value)

    value = property(get_value, set_value)

    _old_value = None

    def get_old_value(self):
        if self._old_value is None:
            return self.get_value()
        return self._old_value

    old_value = property(get_old_value)

    @property
    def is_assigned(self):
        value = self.get_value()
        field = self.attribute.value_field
        if field == 'value_string':
            return value is not None and len(value) > 0
        return value is not None

    def save_value(self):
        # Re-assign product
        self.product = self.product
        if self.is_assigned:
            self.save()
        elif not self.pk is None:
            self.delete()

    def natural_key(self):
        return (self.attribute.natural_key(), self.product.natural_key())
    natural_key.dependencies = ['attribute.attribute', 'product.product']

    def __unicode__(self):
        return call_or_format(modules.attribute.value_format, value=self)

    class Meta:
        abstract = True
        ordering = ['attribute'] + VALUE_FIELDS
        verbose_name = _("value")
        verbose_name_plural = _("values")
    

@load(action='finalize_attribute_Attribute')
def finalize_model():

    choices = list(modules.attribute.Attribute.TYPE_CHOICES)
    for key, typ in modules.attribute.attribute_types.iteritems():
        choices.append((key, typ['verbose_name']))

    class Attribute(modules.attribute.Attribute):
        
        type = AttributeTypeField(
            max_length=255,
            db_index=True,
            choices=choices,
            default=modules.attribute.Attribute.TYPE_STRING
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

    TYPE_STRING = 'string'
    TYPE_INT = 'int'
    TYPE_FLOAT = 'float'
    
    TYPES = [TYPE_STRING, TYPE_INT, TYPE_FLOAT]

    TYPE_CHOICES = (
        (TYPE_STRING, _("string")),
        (TYPE_INT, _("integer")),
        (TYPE_FLOAT, _("float")),
    )

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

        if self.type != old.type:
            raise Exception((_(u"Cannot change attribute type "
                               u"of an attribute that is already in use.")))

        super(Attribute, self).save(*args, **kwargs)

    def parse(self, string):
        if self.type == self.TYPE_STRING:
            return string
        elif self.type == self.TYPE_INT:
            try:
                return int(string)
            except ValueError:
                pass
        elif self.type == self.TYPE_FLOAT:
            return float(string)
        else:
            return self._get_adapter().parse(string) 
        raise ValueError("Could not parse '{0}' for "
                         "attribute '{1}'.".format(string, self))

    @property
    def value_field(self):
        if self.type in self.TYPES:
            return 'value_{0}'.format(self.type)
        return 'value_object'

    @property
    def help_text(self):
        return ''

    @property
    def label(self):
        return self.name.capitalize()

    @property
    def validators(self):
        return []
    
    def _get_adapter(self):
        if self.type in modules.attribute.attribute_types:
            return modules.attribute.attribute_types[self.type]['adapter']
        else:
            raise Exception("Attribute '{0}' with type '{1}' "
                            "has no adapter".format(self.key, self.type))

    @property
    def choices(self):
        return self._get_adapter().get_choices()

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
                .select_related('product__id', 'attribute') \
                .prefetch_value_objects()
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
    modules.product.register('ProductQuerySet', ProductQuerySet)
    modules.product.register('ProductManager', ProductManager)
