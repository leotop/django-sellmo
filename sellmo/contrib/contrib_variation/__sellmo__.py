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
from sellmo.api.decorators import load
from sellmo.magic import ModelMixin
from sellmo.contrib.contrib_variation.models import Option

#

from django.db import models
from django.contrib.contenttypes.models import ContentType
from django.utils.translation import ugettext_lazy as _

#

namespace = apps.variation.namespace

#

@load(action='setup_variants', after='load_subtypes')
def setup_variants():
	pass


@load(action='load_variants', after='setup_variants')
def load_variants():
	
	from sellmo.contrib.contrib_variation.variant import VariantFieldDescriptor, Variant
	apps.variation.Variant = Variant
	for subtype in apps.variation.product_subtypes:
		
		class Meta:
			app_label = 'product'
			verbose_name = _("variant")
			verbose_name_plural = _("variants")
	
		name = '%sVariant' % subtype.__name__
		attr_dict = {
			'product' : models.ForeignKey(
				subtype,
				related_name = 'variants',
				editable = False
			),
			'options' : models.ManyToManyField(
				Option,
				verbose_name = _("options"),
			),
			'Meta' : Meta,
			'__module__' : subtype.__module__
		}
		
		model = type(name, (apps.variation.Variant, apps.product.Product,), attr_dict)
		for field in model.get_variable_fields():
			descriptor = field.model.__dict__.get(field.name, None)
			setattr(model, field.name, VariantFieldDescriptor(field, descriptor=descriptor))
		
		apps.variation.subtypes.append(model)
		setattr(apps.variation, name, model)
	