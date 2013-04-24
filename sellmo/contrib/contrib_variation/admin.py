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

from django.forms import ValidationError
from django.forms.models import ModelForm, BaseInlineFormSet
from django.contrib import admin
from django.utils.translation import ugettext_lazy as _
from django.utils.text import capfirst
from django.utils import six
from django.contrib.admin.sites import NotRegistered
from django.contrib.contenttypes.models import ContentType

#

class AttributeTypeListFilterBase(admin.SimpleListFilter):
	title = _("attribute type")
	parameter_name = 'attribute_type'
	attribute_types = []
	
	def lookups(self, request, model_admin):
		return [(str(content_type.pk), unicode(content_type)) for content_type in ContentType.objects.get_for_models(*self.attribute_types).values()]
		
	def queryset(self, request, queryset):
		attribute_type = self.value()
		if attribute_type != None:
			return queryset.filter(content_type=attribute_type)
		else:
			return queryset.all()
			
class VariantFormSet(BaseInlineFormSet):
	def clean(self):
		if any(self.errors):
		 	return
		variants = []
		for form in self.forms:
			if form.cleaned_data.has_key('options'):
				
				# Enforce unique variants
				options = u'_'.join([u'%s-%s' % (option.variable.name, option.attribute.value) for option in form.cleaned_data['options']])
				if options in variants:
					raise ValidationError(_("Duplicate variants"))
				variants.append(options)
				
			
class VariantForm(ModelForm):
	
	def __init__(self, *args, **kwargs):
		super(VariantForm, self).__init__(*args, **kwargs)
		for field in self.fields:
			self[field].field.required = False
			
	def clean(self):
		cleaned_data = super(VariantForm, self).clean()
		
		# Enforce options
		options = cleaned_data['options']
		if not options:
			raise ValidationError(_("A variant requires options"))
			
		# Enforce unique options
		variables = []
		for option in options:
			if option.variable.name in variables:
				raise ValidationError(_("Select one option"))
			variables.append(option.variable.name)
		
		# Enforce slug
		if cleaned_data.has_key('slug'):
			if not cleaned_data['slug']:
				cleaned_data['slug'] = self.instance.generate_slug(options=cleaned_data['options'], product=cleaned_data['product'])
				self.data[self.add_prefix('slug')] = cleaned_data['slug']
		
		return cleaned_data
		
class VariantInlineMixin(object):
	form = VariantForm
	formset = VariantFormSet
	
	def formfield_for_manytomany(self, db_field, request, **kwargs):
		if db_field.name == 'options':
			kwargs['queryset'] = modules.variation.Option.objects.all().prefetch_related('attribute', 'variable')
		return super(VariantInlineMixin, self).formfield_for_manytomany(db_field, request, **kwargs)
		
class CustomOptionsMixin(object):
	def formfield_for_manytomany(self, db_field, request, **kwargs):
		if db_field.name == 'custom_options':
			kwargs['queryset'] = modules.variation.Option.objects.all().prefetch_related('attribute', 'variable')
		return super(CustomOptionsMixin, self).formfield_for_manytomany(db_field, request, **kwargs)

