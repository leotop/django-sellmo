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
from sellmo.contrib.contrib_attribute.forms import ProductAttributeForm
from sellmo.contrib.contrib_variation.utils import generate_slug

#

class SaveFieldMixin(object):

	def get_deprecated_values(self, recipe, attribute, values):
		field = '%s__in' % (attribute.value_field, )
		kwargs = {
			field : values
		}
		
		q = ~Q(**kwargs) 
		
		return modules.attribute.Value.objects.recipe(exclude=False).filter(attribute=attribute, recipe=recipe).filter(q)
		
	def get_existing_values(self, recipe, attribute, values):
		field = '%s__in' % (attribute.value_field, )
		kwargs = {
			field : values
		}
		
		q = Q(**kwargs) 
		
		return modules.attribute.Value.objects.recipe(exclude=False).filter(attribute=attribute, recipe=recipe).filter(q)

	def save(self, recipe, attribute, values):
		deprecated = self.get_deprecated_values(recipe, attribute, values)
		deprecated.delete()
		
		existing = [value.get_value() for value in self.get_existing_values(recipe, attribute, values)]
		for value in values:
			if not value in existing:
				obj = modules.attribute.Value(product=recipe.product, recipe=recipe, attribute=attribute)
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
		
class ObjectField(forms.ModelMultipleChoiceField, SaveFieldMixin):
	def from_values(self, values):
		return ValueObject.objects.filter(pk__in=[value.get_value().pk for value in values])

class VariationRecipeForm(ModelForm):
	
	FIELD_CLASSES = {
		modules.attribute.Attribute.TYPE_STRING : SeperatedCharField,
		modules.attribute.Attribute.TYPE_INT : SeperatedIntegerField,
		modules.attribute.Attribute.TYPE_OBJECT : ObjectField,
	}
	
	def __init__(self, delay_build=False, *args, **kwargs):
		super(VariationRecipeForm, self).__init__(*args, **kwargs)
		if not delay_build:
			self.build_attribute_fields()
			
	def build_attribute_fields(self, attributes=None):
		
		if attributes is None:
			attributes = modules.attribute.Attribute.objects.filter(variates=True)
			
		# Append attribute fields
		for attribute in attributes:
			
			if not self.instance.pk is None:
				# Get attribute values (if any)
				try:
					values = modules.attribute.Value.objects.recipe(exclude=False).filter(attribute=attribute, recipe=self.instance)
				except modules.attribute.Value.DoesNotExist:
					values = None
			else:
				values = None
				
			defaults = {
				'label' : attribute.name.capitalize(),
				'required' : False,
				'help_text' : attribute.help_text,
				'validators' : attribute.validators,
			}
			
			field = self.FIELD_CLASSES[attribute.type]
			if field is ObjectField:
				field = field(queryset=attribute.get_object_choices(), **defaults)
			else:
				field = field(**defaults)
			
			self.fields[attribute.key] = field
			if values:
				self.initial[attribute.key] = field.from_values(values)
					
	def save(self, commit=True):
		instance = super(VariationRecipeForm, self).save(commit=False)
		
		def save_attributes():
			for attribute in modules.attribute.Attribute.objects.filter(variates=True):
				values = self.cleaned_data.get(attribute.key)
				field = self.FIELD_CLASSES[attribute.type]
				if field is ObjectField:
					field = field(queryset=attribute.get_object_choices())
				else:
					field = field()
				field.save(self.instance, attribute, values)
		
		if commit:
			instance.save()
			save_attributes()
		else:
			self.save_m2m = save_attributes
			
		return instance

class VariantForm(ProductAttributeForm):
	def __init__(self, *args, **kwargs):
		super(VariantForm, self).__init__(delay_build=True, *args, **kwargs)
		for field in self.fields:
			self[field].field.required = False
			
	def clean(self):
		cleaned_data = super(ProductAttributeForm, self).clean()
		
		# Assign attributes
		for attribute in modules.attribute.Attribute.objects.filter(variates=True):
			value = self.cleaned_data.get(attribute.key)
			setattr(self.instance.attributes, attribute.key, value)
		
		# Enforce options
		if not list(self.instance.attributes):
			raise ValidationError(_("A variant requires at least one attribute"))
		
		# Enforce slug
		if cleaned_data.has_key('slug'):
			if not cleaned_data['slug']:
				cleaned_data['slug'] = generate_slug(
					product=cleaned_data['product'],
					values=list(self.instance.attributes),
					unique=False
				)
				self.data[self.add_prefix('slug')] = cleaned_data['slug']
		
		return cleaned_data

class VariantFormSet(BaseInlineFormSet):

	__attributes = None
	def get_attributes(self):
		if self.__attributes is None:
			self.__attributes = modules.attribute.Attribute.objects.filter(variates=True)
		return self.__attributes

	def add_fields(self, form, index):
		super(VariantFormSet, self).add_fields(form, index)
		form.build_attribute_fields(attributes=self.get_attributes())
				