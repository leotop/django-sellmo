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

from sellmo import modules

#

from django.db import models
from django.core.exceptions import ValidationError
from django.utils.translation import ugettext_lazy as _
from django.utils.encoding import smart_text
from django.utils.text import capfirst

# Exceptions

class ProductUnassignedException(Exception):
	pass
	
class DuplicateSlugException(Exception):
	pass
	
#

class VariantMixin(object):
	
	non_variable_fields = ['content_type', 'slug', 'product', 'options']
	non_variable_field_types = [models.BooleanField]
	_variable_fields_enabled = True
	_is_variant = True
	
	@classmethod
	def get_variable_fields(cls):
		for field in cls._meta.fields:
			if not field.auto_created and field.null and not field.name in cls.non_variable_fields and not field.__class__ in cls.non_variable_field_types:
				yield field
				
	def generate_slug(self, options=None, product=None):
		if not options:
			options = self.options
		if not product:
			product = self.product
			
		short = '-'.join([option.attribute.value for option in options])
		full = '_'.join([u'%s-%s' % (option.variable.name, option.attribute.value) for option in options])
		for attributes in [short, full]:
			slug = u'%(prefix)s-%(attributes)s' % {
				'attributes' : attributes,
				'prefix' : product.slug
			}
			if self._is_unique_slug(slug):
				return slug
		return slug
	
	def _is_unique_slug(self, slug):
		try:
			existing = modules.product.Product.objects.polymorphic().get(slug=slug)
		except modules.product.Product.DoesNotExist:
			return True
		return getattr(existing, 'product', None) == self.product
	
	def get_product(self):
		if hasattr(self, 'product_id') and self.product_id != None:
			return self.product		
		return None
		
	def validate_unique(self, exclude=None):
		super(self.__class__.__base__, self).validate_unique(exclude)
		if 'slug' not in exclude:
			if not self._is_unique_slug(self.slug):
				message = _("%(model_name)s with this %(field_label)s already exists.") % {
					'model_name': capfirst(modules.product.Product._meta.verbose_name),
					'field_label': 'slug'
				}
				raise ValidationError({'slug' : [message]})		

	def save(self, *args, **kwargs):
		product = self.get_product()
		if not product:
			raise ProductUnassignedException()
			
		for field in self.__class__.get_variable_fields():
			val = getattr(self, field.name)
			pval = getattr(product, field.name)
			if val == pval:
				setattr(self, field.name, None)
		
		self._variable_fields_enabled = False
		super(VariantMixin, self).save(*args, **kwargs)
		self._variable_fields_enabled = True

	class Meta:
		app_label = 'product'
		verbose_name = _("variant")
		verbose_name_plural = _("variants")
		
	def __unicode__(self):
		product = super(VariantMixin, self).__unicode__()
		if not self.pk is None:
			return u"%s %s" % (product, ", ".join([str(option) for option in self.options.all()]))
		return product
	
class VariantFieldDescriptor(object):
	
	def __init__(self, field, descriptor=None):
		self.field = field
		self.descriptor = descriptor
	
	def __get__(self, obj, objtype):
		if not self.descriptor:
			val = obj.__dict__.get(self.field.name, None)
		else:
			val = self.descriptor.__get__(obj, objtype)

		if not val and obj._variable_fields_enabled:
			product = obj.get_product()
			if product:
				# Get this variant products value
				val = getattr(obj.product, self.field.name)
			
		return val
		
	def __set__(self, obj, val):
		if not self.descriptor:
			obj.__dict__[self.field.name] = val
		else:
			self.descriptor.__set__(obj, val)
			
		
		