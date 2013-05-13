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

#

class AttributeHelper(object):
	
	def __init__(self, product):
		self.__dict__['_product'] = product
		self.__dict__['_values'] = {}
		self.__dict__['_attributes'] = {}
		
	def get_attribute(self, key):
		if not self._attributes.has_key(key):
			try:
				attribute = modules.attribute.Attribute.objects.get(key=key)
			except modules.attribute.Attribute.DoesNotExist:
				self._attributes[key] = None
			else:
				self._attributes[key] = attribute
		
		if self._attributes[key] is None:
			raise AttributeError(key)
		else:
			return self._attributes[key]
		
	def __getattr__(self, name):
		
		try:
			return super(AttributeHelper, self).__getattr__(self, name)
		except AttributeError:
			pass
			
		attribute = self.get_attribute(name)
		if not self._values.has_key(attribute.key):
			try:
				value = modules.attribute.Value.objects.get(attribute=attribute, product=self._product)
			except modules.attribute.Value.DoesNotExist:
				self._values[attribute.key] = modules.attribute.Value(product=product, attribute=attribute)
			else:
				self._values[attribute.key] = value
		return self._values[attribute.key].get_value()
		
	def __setattr__(self, name, value):
		
		try:
			attribute = self.get_attribute(name)
		except AttributeError:
			super(AttributeHelper, self).__setattr__(name, value)
		else:
			if not self._values.has_key(attribute.key):
				self._values[attribute.key] = modules.attribute.Value(attribute=attribute, product=self._product)
			self._values[attribute.key].set_value(value)
		
	def __iter__(self):
		for value in self._values.values():
			if value.is_assigned:
				yield value
		
	def save(self):
		for value in self:
			value.save_value()
			
		# Clean cache
		self._values = {}