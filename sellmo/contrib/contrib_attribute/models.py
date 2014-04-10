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
from django.db.models.query import QuerySet
from django.utils.translation import ugettext_lazy as _

from sellmo import modules
from sellmo.api.decorators import load
from sellmo.core.polymorphism import PolymorphicModel, PolymorphicManager
from sellmo.utils.formatting import call_or_format

from sellmo.contrib.contrib_attribute.config import settings
from sellmo.contrib.contrib_attribute.fields import (AttributeKeyField, 
                                                     AttributeTypeField)
from sellmo.contrib.contrib_attribute.helpers import AttributeHelper


class ValueObject(PolymorphicModel):

    class Meta:
        app_label = 'attribute'
        verbose_name = _("value object")
        verbose_name_plural = _("value objects")


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
@load(after='finalize_product_Product')
@load(before='finalize_attribute_Value')
def load_model():

    class Value(modules.attribute.Value):

        # The attribute to which we belong
        attribute = models.ForeignKey(
            modules.attribute.Attribute,
            db_index=True,
            verbose_name=_(u"attribute"),
            related_name='values',
            on_delete=models.PROTECT
        )

        # The product to which we apply
        product = models.ForeignKey(
            modules.product.Product,
            db_index=True,
            related_name='values',
        )

        class Meta(modules.attribute.Value.Meta):
            abstract = True

    modules.attribute.Value = Value


@load(action='finalize_attribute_Value')
def finalize_model():

    class Value(modules.attribute.Value):

        class Meta(modules.attribute.Value.Meta):
            app_label = 'attribute'
            ordering = ['attribute', 'value_string',
                        'value_int', 'value_float', 'value_object']
            verbose_name = _("value")
            verbose_name_plural = _("values")

    modules.attribute.Value = Value


class ValueQuerySet(QuerySet):

    def for_product(self, product):
        return self.filter(product=product)

    def for_attribute(self, attribute):
        return self.filter(attribute=attribute)


class ValueManager(models.Manager):

    def get_by_natural_key(self, attribute, product):
        return self.get(
            attribute=modules.attribute.Attribute.get_by_natural_key(
                *attribute),
            product=modules.product.Product.get_by_natural_key(*product)
        )

    def get_query_set(self):
        return ValueQuerySet(self.model)

    def for_product(self, *args, **kwargs):
        return self.get_query_set().for_product(*args, **kwargs)

    def for_attribute(self, *args, **kwargs):
        return self.get_query_set().for_attribute(*args, **kwargs)


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
        ValueObject,
        null=True,
        blank=True,
        db_index=True,
        on_delete=models.PROTECT
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
            return not value is None and len(value) > 0
        return not value is None

    @property
    def template(self):
        type = self.attribute.type
        if self.attribute.type == Attribute.TYPE_OBJECT:
            type = self.value.__class__.__name__
        return 'attribute/%s.html' % type.lower()

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
        return call_or_format(settings.VALUE_FORMAT, value=self)

    class Meta:
        abstract = True


@load(action='finalize_attribute_Attribute')
def finalize_model():

    class Attribute(modules.attribute.Attribute):
        object_choices = models.ManyToManyField(
            ValueObject,
            blank=True
        )

        class Meta(modules.attribute.Attribute.Meta):
            app_label = 'attribute'
            ordering = ['sort_order', 'name']
            verbose_name = _("attribute")
            verbose_name_plural = _("attributes")

    modules.attribute.Attribute = Attribute


class AttributeQuerySet(QuerySet):

    def for_product(self, product):
        return self.filter(values__product=product).distinct()


class AttributeManager(models.Manager):

    def get_by_natural_key(self, key):
        return self.get(key=key)

    def get_query_set(self):
        return AttributeQuerySet(self.model)

    def for_product(self, *args, **kwargs):
        return self.get_query_set().for_product(*args, **kwargs)


class Attribute(models.Model):

    objects = AttributeManager()

    TYPE_STRING = 'string'
    TYPE_INT = 'int'
    TYPE_FLOAT = 'float'
    TYPE_OBJECT = 'object'

    TYPES = (
        (TYPE_STRING, _("string")),
        (TYPE_INT, _("integer")),
        (TYPE_FLOAT, _("float")),
        (TYPE_OBJECT, _("object")),
    )

    name = models.CharField(
        max_length=100
    )

    key = AttributeKeyField(
        max_length=50,
        db_index=True,
        blank=True
    )

    type = AttributeTypeField(
        max_length=50,
        db_index=True,
        choices=TYPES,
        default=TYPE_STRING
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

        if self.type != old.type:
            raise Exception((_(u"Cannot change attribute type "
                               u"of an attribute that is already in use.")))

        super(Attribute, self).save(*args, **kwargs)

    def parse(self, string):
        if self.type == self.TYPE_STRING:
            return string
        elif self.type in (self.TYPE_INT, self.TYPE_OBJECT):
            try:
                return int(string)
            except ValueError:
                pass
        elif self.type == self.TYPE_FLOAT:
            return float(string)
        raise ValueError(
            "Could not parse '%s' for attribute '%s'." % (string, self))

    @property
    def value_field(self):
        return 'value_%s' % (self.type,)

    @property
    def help_text(self):
        return ''

    @property
    def label(self):
        return self.name.capitalize()

    @property
    def validators(self):
        return []

    __object_choices = None

    def get_object_choices(self):
        if self.__object_choices is None:
            self.__object_choices = self.object_choices.polymorphic().all()
        return self.__object_choices

    def save(self, *args, **kwargs):
        if not self.key:
            self.key = AttributeKeyField.create_key_from_name(self.name)
        super(Attribute, self).save(*args, **kwargs)

    def natural_key(self):
        return (self.key,)

    def __unicode__(self):
        return self.name

    class Meta:
        abstract = True
