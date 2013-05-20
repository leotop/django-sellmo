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

#

class ProductAttributeForm(ModelForm):

	FIELD_CLASSES = {
		modules.attribute.Attribute.TYPE_STRING : forms.CharField,
		modules.attribute.Attribute.TYPE_INT : forms.IntegerField,
		modules.attribute.Attribute.TYPE_OBJECT : forms.ModelChoiceField,
	}
	
	def __init__(self, *args, **kwargs):
		delay_build = False
		if kwargs.has_key('delay_build'):
			delay_build = kwargs.pop('delay_build')
		
		super(ProductAttributeForm, self).__init__(*args, **kwargs)
		
		if not delay_build:
			self.build_attribute_fields()
			
	def build_attribute_fields(self, attributes=None):
		
		if attributes is None:
			attributes = modules.attribute.Attribute.objects.all()
			
		# Append attribute fields
		for attribute in attributes:
			# Get attribute value (if any)
			try:
				value = modules.attribute.Value.objects.get(attribute=attribute, product=self.instance)
			except modules.attribute.Value.DoesNotExist:
				value = None
				
			defaults = {
				'label' : attribute.name.capitalize(),
				'required' : attribute.required,
				'help_text' : attribute.help_text,
				'validators' : attribute.validators,
			}
			
			field = self.FIELD_CLASSES[attribute.type]
			if field is forms.ModelChoiceField:
				field = field(queryset=attribute.get_object_choices(), **defaults)
			else:
				field = field(**defaults)
			
			self.fields[attribute.key] = field
			if value:
				self.initial[attribute.key] = getattr(self.instance.attributes, attribute.key)
				
	def save(self, commit=True):
		instance = super(ProductAttributeForm, self).save(commit=False)
		
		# Assign attributes
		for attribute in modules.attribute.Attribute.objects.all():
			value = self.cleaned_data.get(attribute.key)
			setattr(instance.attributes, attribute.key, value)
		
		if commit:
			instance.save()
			
		return instance