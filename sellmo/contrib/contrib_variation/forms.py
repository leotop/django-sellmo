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

#

from django.db.models import Q
from django import forms
from django.forms import ValidationError
from django.forms.models import ModelForm, BaseInlineFormSet
from django.contrib import admin
from django.utils.translation import ugettext_lazy as _
from django.utils.text import capfirst
from django.utils import six
from django.contrib.admin.sites import NotRegistered
from django.contrib.admin.widgets import ForeignKeyRawIdWidget
from django.contrib.contenttypes.models import ContentType
from django.core.validators import EMPTY_VALUES

#

from sellmo.contrib.contrib_attribute.models import ValueObject
from sellmo.contrib.contrib_attribute.forms import ProductAttributeFormFactory
from sellmo.contrib.contrib_variation.utils import generate_slug

#

class SaveFieldMixin(object):

    def get_deprecated_values(self, product, attribute, values):
        field = '%s__in' % (attribute.value_field, )
        kwargs = {
            field : values
        }
        
        q = ~Q(**kwargs) 
        
        return modules.attribute.Value.objects.filter(attribute=attribute, product=product, variates=True).filter(q)
        
    def get_existing_values(self, product, attribute, values):
        field = '%s__in' % (attribute.value_field, )
        kwargs = {
            field : values
        }
        
        q = Q(**kwargs) 
        
        return modules.attribute.Value.objects.filter(attribute=attribute, product=product, variates=True).filter(q)

    def save(self, product, attribute, values):
        deprecated = self.get_deprecated_values(product, attribute, values)
        deprecated.delete()
        
        existing = [value.get_value() for value in self.get_existing_values(product, attribute, values)]
        for value in values:
            if not value in existing:
                obj = modules.attribute.Value(product=product, variates=True, attribute=attribute)
                obj.set_value(value)
                obj.save()

class SeperatedInputField(forms.Field):
    
    def __init__(self, field, seperator=u'|', **kwargs):
        super(SeperatedInputField, self).__init__(**kwargs)
        self._field = field(**kwargs)
        self._seperator = seperator
    
    def from_values(self, values):
        return self._seperator.join([unicode(value.get_value()) for value in values])
        
    def to_python(self, value):
        result = []
        value = super(SeperatedInputField, self).to_python(value)
        if value in EMPTY_VALUES:
            return result
        values = value.split(self._seperator)       
        for value in values:
            result.append(self._field.clean(value))
            
        return result
        
class SeperatedCharField(SeperatedInputField, SaveFieldMixin):
    def __init__(self, **kwargs):
        super(SeperatedCharField, self).__init__(field=forms.CharField, **kwargs) 
    
class SeperatedIntegerField(SeperatedInputField, SaveFieldMixin):
    def __init__(self, **kwargs):
        super(SeperatedIntegerField, self).__init__(field=forms.IntegerField, **kwargs)
        
class SeperatedFloatField(SeperatedInputField, SaveFieldMixin):
    def __init__(self, **kwargs):
        super(SeperatedFloatField, self).__init__(field=forms.FloatField, **kwargs)
        
class ObjectField(forms.ModelMultipleChoiceField, SaveFieldMixin):
    def from_values(self, values):
        return ValueObject.objects.filter(pk__in=[value.get_value().pk for value in values])

class ProductVariationFormFactory(ProductAttributeFormFactory):
    
    FIELD_CLASSES = {
        modules.attribute.Attribute.TYPE_STRING : SeperatedCharField,
        modules.attribute.Attribute.TYPE_INT : SeperatedIntegerField,
        modules.attribute.Attribute.TYPE_FLOAT : SeperatedFloatField,
        modules.attribute.Attribute.TYPE_OBJECT : ObjectField,
    }
    
    def get_attributes(self):
        return modules.attribute.Attribute.objects.filter(variates=True)
        
    def get_attribute_field_args(self, attribute, field):
        args = []
        if field is ObjectField:
            args.append(attribute.get_object_choices())
        
        return args

class ProductVariationFormMixin(object):
    
    def __init__(self, *args, **kwargs):
        initial = {}
        if 'initial' in kwargs:
            initial = kwargs['initial']
        instance = None
        if 'instance' in kwargs:
            instance = kwargs['instance']
        if instance:
            initial.update({
                self.__attribute_field_names[key] : value for key, value in self.__get_values(instance).iteritems()
            })
        kwargs['initial'] = initial
        super(ProductVariationFormMixin, self).__init__(*args, **kwargs)
        
    def __get_values(self, product):
        result = {}
        for attribute in self.__attributes:
            if product.pk is not None:
                try:
                    values = modules.attribute.Value.objects.filter(attribute=attribute, product=product, variates=True)
                except modules.attribute.Value.DoesNotExist:
                    values = None
            else:
                values = None
            
            field = self.__attribute_fields[attribute.key]
            result[attribute.key] = field.from_values(values)
        return result
    
    def save(self, commit=True):
        instance = super(ProductVariationFormMixin, self).save(commit=False)
        def save_variations():
            for attribute in self.__attributes:
                values = self.cleaned_data.get(self.__attribute_field_names[attribute.key])
                field = self.__attribute_fields[attribute.key]
                field.save(instance, attribute, values)
        if commit:
            instance.save()
            save_variations()
        else:
            self.save_variations = save_variations
        return instance

class VariantAttributeFormMixin(object):
    
    def __init__(self, *args, **kwargs):
        initial = {}
        if 'initial' in kwargs:
            initial = kwargs['initial']
        instance = None
        if 'instance' in kwargs:
            instance = kwargs['instance']
        if instance:
            initial.update({
                self.__attribute_field_names[attribute.key] : instance.attributes[attribute.key] 
                for attribute in self.__attributes
            })
        kwargs['initial'] = initial
        super(VariantAttributeFormMixin, self).__init__(*args, **kwargs)
        for field in self.fields:
            self[field].field.required = False
    
    def save(self, commit=True):
        instance = super(VariantAttributeFormMixin, self).save(commit=False)
        instance.product = self.cleaned_data['product']
        for attribute in self.__attributes:
            value = self.cleaned_data.get(self.__attribute_field_names[attribute.key])
            instance.attributes[attribute.key] = value
        if commit:
            instance.save()
        return instance
            
    def clean(self):
        cleaned_data = super(VariantAttributeFormMixin, self).clean()
        
        # Temporary collect values to generate slug
        # Get only the values which variate
        values = []
        for attribute in self.__attributes.filter(variates=True):
            value = modules.attribute.Value(attribute=attribute)
            value.value = self.cleaned_data.get(self.__attribute_field_names[attribute.key])
            if value.is_assigned:
                values.append(value)
        
        # Enforce at least one variated value
        if not values:
            raise ValidationError(_("A variant requires at least one variated attribute"))
        
        # Generate slug if needed
        if cleaned_data.has_key('slug'):
            if not cleaned_data['slug']:
                cleaned_data['slug'] = generate_slug(
                    product=cleaned_data['product'],
                    values=values,
                    unique=False
                )
                self.data[self.add_prefix('slug')] = cleaned_data['slug']
        
        return cleaned_data
                