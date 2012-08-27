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

import types

#

from django.db import models
from django.db.models.query import QuerySet
from django.contrib.contenttypes.models import ContentType

#

class PolymorphicQuerySet(QuerySet):
			
	def iterator(self):
		for item in super(PolymorphicQuerySet, self).iterator():
			yield item.cast()
			
class PolymorphicManager(models.Manager):
	def get_query_set(self):
		return PolymorphicQuerySet(self.model, using=self._db)

class PolymorphicModel(models.Model):
	
	content_type = models.ForeignKey(ContentType, editable=False, null=True)
	objects = PolymorphicManager()
	
	def save(self):
		if not self.content_type:
			self.content_type = ContentType.objects.get_for_model(self.__class__)
		self.save_base()
		
	def cast(self):
		content_type = self.content_type
		model = content_type.model_class()
		if(model == self.__class__):
			return self
		return model.objects.get(id=self.id)
		
	class Meta:
		abstract = True