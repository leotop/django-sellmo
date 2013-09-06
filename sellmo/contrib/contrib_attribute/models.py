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
from django.db.models.query import QuerySet
from django.utils.translation import ugettext_lazy as _

#

from sellmo import modules
from sellmo.api.decorators import load
from sellmo.utils.polymorphism import PolymorphicModel, PolymorphicManager

#

from sellmo.contrib.contrib_attribute.fields import AttributeKeyField, AttributeTypeField
from sellmo.contrib.contrib_attribute.helpers import AttributeHelper

class ValueObject(PolymorphicModel):
    class Meta:
        app_label = 'attribute'
        
@load(before='finalize_product_Product')
def load_model():
    class Product(modules.product.Product):
    
        def __init__(self, *args, **kwargs):
            super(Product, self).__init__(*args, **kwargs)
            self.attributes = AttributeHelper(self)
            
        def save(self, *args, **kwargs):
            super(Product, self).save(*args, **kwargs)
            self.attributes.save()
    
        class Meta:
            abstract = True
        
    modules.product.Product = Product
    
@load(action='finalize_attribute_Value')
@load(after='finalize_attribute_Attribute')
@load(after='finalize_product_Product')
def finalize_model():
    
    class Value(modules.attribute.Value):
        
        # The attribute to which we belong
        attribute = models.ForeignKey(
            modules.attribute.Attribute,
            db_index = True,
            verbose_name=_(u"attribute"),
            related_name = 'values',
            on_delete = models.PROTECT
        )
    
        # The product to which we apply
        product = models.ForeignKey(
            modules.product.Product,
            db_index = True,
            related_name = '+',
        )
        
        # Possible value object
        value_object = models.ForeignKey(
            ValueObject,
            null = True,
            blank = True,
            db_index = True,
            on_delete = models.PROTECT
        )
        
        class Meta:
            app_label = 'attribute'
    
    modules.attribute.Value = Value
    
class ValueQuerySet(QuerySet):
    def for_product(self, product):
        return self.filter(product=product)
        
    def for_attribute(self, attribute):
        return self.filter(attribute=attribute)
    
class ValueManager(models.Manager):
    def get_query_set(self):
        return ValueQuerySet(self.model)
        
    def for_product(self, *args, **kwargs):
        return self.get_query_set().for_product(*args, **kwargs)
        
    def for_attribute(self, *args, **kwargs):
        return self.get_query_set().for_attribute(*args, **kwargs)
    
class Value(models.Model):

    objects = ValueManager()
    
    value_int = models.IntegerField(
        null = True,
        blank = True,
    )
    
    value_string = models.CharField(
        max_length = 255,
        null = True,
        blank = True,
    )
    
    __value_object = None
    @property
    def _value_object(self):
        if self.value_object and self.__value_object is None:
            self.__value_object = self.value_object.downcast()
        return self.__value_object
    
    def __unicode__(self):
        return u"%s -> %s : %s" % (self.product, self.attribute, self.get_value())
        
    def get_value(self):
        field = self.attribute.value_field
        if field == 'value_object':
            return self._value_object
        
        return getattr(self, field)
        
    def set_value(self, value):
        field = self.attribute.value_field
        if field == 'value_object':
            self.__value_object = None
        setattr(self, field, value)
        
    value = property(get_value, set_value)
    
    @property
    def is_assigned(self):
        value = self.get_value()
        field = self.attribute.value_field
        if field == 'value_string':
            return not value is None and len(value) > 0
        return not value is None
        
    @property
    def template(self):
        return modules.attribute.get_value_template(value=self)
        
    def save_value(self):
        # Re-assign product
        self.product = self.product
        if self.is_assigned:
            self.save()
        elif not self.pk is None:
            self.delete()
    
    class Meta:
        abstract = True
        ordering = ['attribute', 'value_string', 'value_int', 'value_object']
        verbose_name = _("value")
        verbose_name_plural = _("values")

@load(action='finalize_attribute_Attribute')
def finalize_model():
    
    class Attribute(modules.attribute.Attribute):
        object_choices = models.ManyToManyField(
            ValueObject,
            blank = True
        )
        
        class Meta:
            app_label = 'attribute'
    
    modules.attribute.Attribute = Attribute
    
class AttributeQuerySet(QuerySet):
    def for_product(self, product):
        return self.filter(values__product=product).distinct()

class AttributeManager(models.Manager):
    def get_query_set(self):
        return AttributeQuerySet(self.model)
    
    def for_product(self, *args, **kwargs):
        return self.get_query_set().for_product(*args, **kwargs)
    
class Attribute(models.Model):
    
    objects = AttributeManager()
    
    TYPE_STRING = 'string'
    TYPE_INT = 'int'
    TYPE_OBJECT = 'object'
    
    TYPES = (
        (TYPE_STRING, _("string")),
        (TYPE_INT, _("integer")),
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
        choices = TYPES,
        default = TYPE_STRING
    )
    
    required = models.BooleanField(
        default=False
    )
    
    sort_order = models.SmallIntegerField(
        default = 0,
        verbose_name = _("sort order"),
    )
    
    def parse(self, string):
        if self.type == self.TYPE_STRING:
            return string
        elif self.type in (self.TYPE_INT, self.TYPE_OBJECT):
            try:
                return int(string)
            except ValueError:
                pass
        raise ValueError("Could not parse '%s' for attribute '%s'." % (string, self))
    
    @property
    def value_field(self):
        return 'value_%s' % (self.type,)
    
    @property
    def help_text(self):
        return ''
        
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
    
    def __unicode__(self):
        return self.name

    class Meta:
        abstract = True
        ordering = ['sort_order', 'name']
        verbose_name = _("attribute")
        verbose_name_plural = _("attributes")
        
# Init modules
from sellmo.contrib.contrib_attribute.modules import *