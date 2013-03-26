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
from sellmo.utils.polymorphism import PolymorphicModel, PolymorphicManager

# Init modules
from sellmo.contrib.contrib_variation.modules import *

#

from django.db import models
from django.utils.translation import ugettext_lazy as _

#

class AttributeManager(PolymorphicManager):
	def get_by_natural_key(self, value):
		return self.get(value=value)

class Attribute(PolymorphicModel):
	
	objects = AttributeManager()
	
	value = models.SlugField(
		max_length = 80,
		db_index = True,
		unique = True,
		verbose_name = _("value"),
	)
	
	def natural_key(self):
		return (self.value,)
	
	def __unicode__(self):
		return self.value
	
	class Meta:
		app_label = 'product'
		ordering = ['content_type', 'value']
		verbose_name = _("attribute")
		verbose_name_plural = _("attributes")
	
class VariableManager(models.Manager):
	def get_by_natural_key(self, name):
		return self.get(name=name)
		
class Variable(models.Model):
	
	objects = VariableManager()
	
	name = models.CharField(
		max_length = 80,
		unique = True,
		verbose_name = _("name"),
	)
	
	attributes = models.ManyToManyField(
		Attribute,
		through = 'Option',
		verbose_name = _("attributes"),
	)
	
	def natural_key(self):
		return (self.name,)
	
	def __unicode__(self):
		return self.name
	
	class Meta:
		app_label = 'product'
		ordering = ['name']
		verbose_name = _("variable")
		verbose_name_plural = _("variables")
		
class OptionManager(models.Manager):
	def get_by_natural_key(self, variable, attribute):
		return self.get(variable=Variable.objects.get_by_natural_key(variable), attribute=Attribute.objects.get_by_natural_key(attribute))
		
class Option(models.Model):
	
	objects = OptionManager()
	
	sort_order = models.PositiveSmallIntegerField(
		verbose_name = _("sort order"),
	)
	
	variable = models.ForeignKey(
		Variable,
		verbose_name = _("variable"),
	)
	
	attribute = models.ForeignKey(
		Attribute,
		verbose_name = _("attribute"),
	)
	
	def natural_key(self):
		return self.variable.natural_key() + self.attribute.natural_key()
	
	def __unicode__(self):
		return u"%s: %s" % (self.variable.name, unicode(self.attribute))
	
	class Meta:
		app_label = 'product'
		unique_together = (('variable', 'attribute'),)
		ordering = ['variable', 'sort_order']
		verbose_name = _("option")
		verbose_name_plural = _("options")