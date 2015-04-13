# Copyright (c) 2014, Adaptiv Design
# All rights reserved.
# 
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:

# 1. Redistributions of source code must retain the above copyright notice,
# this list of conditions and the following disclaimer.

# 2. Redistributions in binary form must reproduce the above copyright notice,
# this list of conditions and the following disclaimer in the documentation
# and/or other materials provided with the distribution.

# 3. Neither the name of the copyright holder nor the names of its contributors
# may be used to endorse or promote products derived from this software without
# specific prior written permission.

# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
# ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE
# LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR
# CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF
# SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS
# INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN
# CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)
# ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
# POSSIBILITY OF SUCH DAMAGE.


from sellmo import modules
from sellmo.contrib.attribute \
     .helpers import AttributeHelper as AttributeHelperBase

from django.db import models
from django.core.exceptions import ValidationError
from django.utils.translation import ugettext_lazy as _
from django.utils.encoding import smart_text
from django.utils.text import capfirst


class AttributeHelper(AttributeHelperBase):
    
    def populate(self, values=None, attributes=None):
        if values is None:
            values = self._product.values.filter(variates=False)
        super(AttributeHelper, self).populate(values, attributes)

    def get_value(self, key):
        # Make sure attribute exists
        attribute = self.get_attribute(key)
        if attribute.key not in self._values and not self._populated:
            try:
                # Special query at this point variates=False
                value = modules.attribute.Value.objects.get(
                    attribute=attribute, product=self._product, variates=False)
            except modules.attribute.Value.DoesNotExist:
                pass
            else:
                self._values[attribute.key] = value
        
        # Create a new value if none found
        if attribute.key not in self._values:
            self._values[attribute.key] = modules.attribute.Value(
                product=self._product, attribute=attribute)
                
        return self._values[attribute.key]


class VariantAttributeHelper(AttributeHelper):

    def get_value_value(self, key):
        value = self.get_value(key)
        if value.is_empty():
            value = self._product.product.attributes.get_value(key)
        return value.value

    def set_value_value(self, key, value):
        product_value = self._product.product.attributes.get_value(key)
        if product_value.value == value or product_value.old_value == value:
            # Make sure variant doesn't have this value set
            self.get_value(key).value = None
        else:
            # Make sure we have this value set
            self.get_value(key).value = value

    def __iter__(self):
        values = {}
        for value in super(VariantAttributeHelper, self).__iter__():
            values[value.attribute.key] = value
        for value in self._product.product.attributes:
            if value.attribute.key not in values:
                values[value.attribute.key] = value
        for value in values.values():
            if not value.is_empty():
                yield value


class VariationAttributeHelper(object):
    
    def __init__(self, variation):
        self._variation = variation
        self._values = {}
        self._populated = False
        
    def populate(self):
        if self._populated:
            return
        variant = self._variation.variant.downcast()
        self._values = {}
        self._populated = True
        for value in self._variation.values.all():
            self._values[value.attribute.key] = value
        for value in variant.attributes:
            if value.attribute.key not in self._values:
                self._values[value.attribute.key] = value
    
    def __iter__(self):
        self.populate()
        for value in self._values.values():
            if not value.is_empty():
                yield value
