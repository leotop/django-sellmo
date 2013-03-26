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
from sellmo.api.decorators import load

#

from django.db import models
from django.utils.translation import ugettext_lazy as _

#

@load(action='finalize_category_Category')
def finalize_model():
	class Category(modules.category.Category):
		pass
	modules.category.Category = Category
	
@load(before='finalize_product_Product', after='finalize_category_Category')
def load_model():
	class Product(modules.product.Product):
		category = models.ManyToManyField(
			modules.category.Category,
			blank = True,
			null = True,
			related_name = 'products',
			verbose_name = _("category"),
		)
		
		class Meta:
			abstract = True
		
	modules.product.Product = Product

class Category(models.Model):
	
	order = models.PositiveSmallIntegerField(
		default = 0,
		editable = False
	)
	
	parent = models.ForeignKey(
		'self',
		blank = True,
		null = True,
		verbose_name = _("parent"),
		related_name = 'children'
	)
	
	name = models.CharField(
		max_length = 255,
		verbose_name = _("name"),
	)
	
	slug = models.SlugField(
		max_length = 80,
		db_index = True,
		verbose_name = _("slug"),
		help_text = _(
			"Slug will be used in the address of"
			" the category page. It should be"
			" URL-friendly (letters, numbers,"
			" hyphens and underscores only) and"
			" descriptive for the SEO needs."
		)
	)
	
	active = models.BooleanField(
		default = True,
		verbose_name = _("active"),
		help_text = (
			"Inactive categories will be hidden from the site."
		)
	)
	
	@property
	def parents(self):
		parents = []
		parent = self.parent
		while parent:
			parents.append(parent)
			parent = parent.parent
			
		parents.reverse()
		return parents
		
	@property
	def descendants(self):
		descendants = []
		for child in self.children.all():
			descendants.append(child)
			descendants.extend(child.descendants)
		return descendants
		
	@property
	def full_name(self):
		categories = self.parents + [self]
		return " | ".join(category.name for category in categories)
		
	@classmethod
	def reorder(cls):
		categories = sorted([ (unicode(x), x) for x in cls.objects.all() ])
		for i in range(len(categories)):
			full_description, category = categories[i]
			category.order = i
			super(Category, category).save()
	
	def save(self, *args, **kwargs):
		super(Category, self).save(*args, **kwargs)
		self.reorder()
	
	def clean(self):
		parent = self.parent
		while parent:
			if parent.id == self.id:
				raise ValidationError(_("Parent assignment causes a loop."))
			parent = parent.parent
	
	def __unicode__(self):
		return self.full_name
	
	class Meta:
		app_label = 'category'
		verbose_name = _("category")
		verbose_name_plural = _("categories")
		ordering = ['order']
		abstract = True
		
# Init modules
from sellmo.contrib.contrib_category.modules import *