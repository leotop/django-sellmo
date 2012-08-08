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

import reaktor

#

from sellmo import apps
from sellmo.api.decorators import load

#

from . models import InvalidationMetaBase, ProductType, Attribute

#

from django.db import models
from django.db.models.signals import post_save, post_delete

#

namespace = apps.product.namespace
apps.product.inlines = []

#

@load(after='alter_product_Product')
def load_models():
	
	class Variant(apps.product.Product):
		
		product = models.ForeignKey(
			apps.product.Product,
			related_name = 'variants'
		)
		
		class Meta:
			app_label = 'product'
		
		class ReflectionMeta(reaktor.ReflectionMeta):
			
			def get_reflector(self, type_id):
				return ProductType.objects.get(id=type_id).variant_reflector()
				
			def provide_type_ids(self):
				for type in ProductType.objects.all():
					yield type.id
					
		class InvalidationMeta(InvalidationMetaBase):
			
			def hookup(self, invalidation_callback):
				post_save.connect(invalidation_callback, sender=ProductType)
				post_delete.connect(invalidation_callback, sender=ProductType)
				post_save.connect(invalidation_callback, sender=Attribute)
				post_delete.connect(invalidation_callback, sender=Attribute)
		
	
	apps.product.Variant = Variant
	reaktor.manager.hookup_base(apps.product.Variant)
	reaktor.manager.hookup_base(apps.product.Product)
