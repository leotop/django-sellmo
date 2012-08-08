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

from sellmo import apps

#

from django.db import models
from django.db.models import Q
from django.db.models.signals import post_save, post_delete
from django.contrib import admin
from django.utils.translation import ugettext_lazy as _

#

import reaktor

#

class InvalidationMetaBase(reaktor.InvalidationMeta):
	
	def _get_linked_types(self, initial):
		linked = [initial.id]
		for type in initial.subtypes.all():
			linked.extend(self._get_linked_types(type))
			
		return linked
	
	def _ids_by_product_type(self, type):
		return self._get_linked_types(type)
			
	def _ids_by_attribute(self, attribute):
		try:
			type = attribute.product_type
		except ProductType.DoesNotExist:
			return []
			
		return self._get_linked_types(type)
	
	def provide_type_ids(self, instance, *args, **kwargs):
	
		if isinstance(instance, ProductType):
			return self._ids_by_product_type(instance)
		elif isinstance(instance, Attribute):
			return self._ids_by_attribute(instance)
		else:
			raise Exception("""Invalid instance type""")
	
	def provide_instructions(self, type_id, instance, *args, **kwargs):
		
		if isinstance(instance, ProductType):
			
			try:
				product_type = ProductType.objects.get(id=type_id)
			except ProductType.DoesNotExist:
				print 'REMOVED A'
				yield reaktor.InvalidationInstruction(remove_model=True)
				return
			
			if kwargs.has_key('created') and not kwargs['created']:
				if instance.id == type_id and instance.identifier.lower() != reaktor.manager.get_model(apps.product.Product, type_id)._meta.object_name.lower():
					print 'REMOVED B'
					yield reaktor.InvalidationInstruction(remove_model=True)
			
		# in case of attribute deletion or no deletion at all
		yield reaktor.InvalidationInstruction()

class Product(apps.product.Product):
		
	class Meta:
		app_label = 'product'
		abstract = True
		
	class ReflectionMeta(reaktor.ReflectionMeta):
		
		def get_reflector(self, type_id):
			return ProductType.objects.get(id=type_id).product_reflector()
			
		def provide_type_ids(self):
			for type in ProductType.objects.all():
				yield type.id
				
		def has_admin(self, type_id):
			return not ProductType.objects.get(id=type_id).intermediary
			
	class InvalidationMeta(InvalidationMetaBase):
		
		def hookup(self, invalidation_callback):
			post_save.connect(invalidation_callback, sender=ProductType)
			post_delete.connect(invalidation_callback, sender=ProductType)
			post_save.connect(invalidation_callback, sender=Attribute)
			post_delete.connect(invalidation_callback, sender=Attribute)


class ProductType(models.Model):
	
	identifier = models.SlugField(
		max_length = 80,
		db_index = True,
		unique = True,
		verbose_name = _("identifier"),
		help_text = _(
			"Identifier will be used as a means to"
			" access this product type."
		)
	)
	
	extends = models.ForeignKey(
		'self',
		related_name= 'subtypes',
		null = True,
		blank = True,
	)
	
	intermediary = models.BooleanField(
		default = False,
		help_text = _(
			"Intermediary product types are not available as actual products. Intermediary product types could come in handy for attribute inheritance."
		)
	)
	
	class Meta:
		app_label = 'product'
	
	def __unicode__(self):
		return self.identifier
	
	#
		
	def variant_reflector(self):
		return self.VariantReflector(self.id, apps.product.Variant)
		
	class VariantReflector(reaktor.Reflector):
	
		def get_model_attributes(self):
			product_type = ProductType.objects.get(id=self.type_id)
			
			class Meta:
				app_label = 'product'
				verbose_name = product_type.identifier
				
			yield reaktor.ModelAttribute('Meta', Meta)
				
			current_type = product_type
			while current_type:
				for attribute in current_type.attribute_set.filter(variates=True):
					yield reaktor.ModelAttribute(attribute.identifier, attribute.field)
					
				current_type = current_type.extends
			
		def get_model_name(self):
			product_type = ProductType.objects.get(id=self.type_id)
			return '%s_variant' % product_type.identifier
	
	def product_reflector(self):
		return self.ProductReflector(self.id, apps.product.Product, apps.product.ProductAdmin)
	
	class ProductReflector(reaktor.Reflector):
	
		def get_model_name(self):
			product_type = ProductType.objects.get(id=self.type_id)
			return product_type.identifier
	
		def get_model_attributes(self):
			product_type = ProductType.objects.get(id=self.type_id)
			
			class Meta:
				app_label = 'product'
				verbose_name = product_type.identifier
				
			yield reaktor.ModelAttribute('Meta', Meta)
			
			current_type = product_type
			while current_type:
				for attribute in current_type.attribute_set.filter(variates=False):
					yield reaktor.ModelAttribute(attribute.identifier, attribute.field)
					
				current_type = current_type.extends
			
		def get_admin_attributes(self, model):
		
			product_type = ProductType.objects.get(identifier=model._meta.object_name.lower())
			variant = reaktor.manager.get_model(apps.product.Variant, product_type.id)
			
			class VariantInline(admin.StackedInline):
				model = variant
				fk_name = 'product'
				extra = 3
		
			yield reaktor.AdminAttribute('inlines', apps.product.inlines + [VariantInline])
		
class AttributeType(models.Model):
	
	description = models.CharField(
		max_length = 80,
		verbose_name = _("description"),
	)
	
	type = models.CharField(
		max_length = 10,
		choices = (
			('select', _("select")),
			('mselect', _("multi select")),
		)
	)
	
	sort_order = models.PositiveSmallIntegerField(
		default = 0,
		verbose_name = _("sort order")
	)
	
	class Meta:
		app_label = 'product'
	
	@property
	def field(self):
		if self.type == 'select':
			return models.ForeignKey(
				AttributeOption,
				on_delete = models.SET_NULL,
				limit_choices_to = { 'attribute_type' : self },
				blank = True,
				null = True
			)
		elif self.type == 'mselect':
			return models.ManyToManyField(
				AttributeOption,
				limit_choices_to = { 'attribute_type' : self },
				blank = True,
				null = True
			)
	
	def __unicode__(self):
		return self.description
		
class AttributeOption(models.Model):
	
	attribute_type = models.ForeignKey(
		'AttributeType'
	)
	
	value = models.CharField(
		max_length = 255,
	)
	
	display = models.CharField(
		max_length = 255,
		help_text = _(
			"User friendly name for this option."
		)
	)
	
	class Meta:
		app_label = 'product'
	
	def __unicode__(self):
		return self.display
	
class Attribute(models.Model):
	
	product_type = models.ForeignKey(
		'ProductType'
	)
	
	attribute_type = models.ForeignKey(
		'AttributeType'
	)
	
	identifier = models.SlugField(
		max_length = 80,
		db_index = True,
		verbose_name = _("identifier"),
		help_text = _(
			"Identifier will be used as a means to"
			" access this attribute."
		)
	)
	
	display = models.CharField(
		max_length = 255,
		verbose_name = _("display name"),
		help_text = _(
			"User friendly name for this attribute."
		)
	)
	
	variates = models.BooleanField(
		verbose_name = _("variates"),
		help_text = _(
			"If yes, this attribute will be used in variations."
		)
	)
	
	role = models.CharField(
		max_length = 20,
		db_index = True,
		verbose_name = _("role"),
		help_text = _(
			"The role which this attribute will fulfil."
		)
	)
	
	@property
	def field(self):
		return self.attribute_type.field
		
	class Meta:
		app_label = 'product'
	
	def __unicode__(self):
		return self.identifier
		
#

apps.product.Product = Product