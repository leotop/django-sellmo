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

from django.db import models
from django.core.exceptions import ValidationError
from django.utils.translation import ugettext_lazy as _
from django.utils.encoding import smart_text
from django.utils.text import capfirst


class AttributeHelper(object):
    
    def __init__(self, product):
        self._product = product
        self._values = {}
        self._attributes = {}
        self._populated = False
    
    def get_attribute(self, key):
        if not self._attributes.has_key(key) and not self._populated:
            try:
                attribute = modules.attribute.Attribute.objects.get(key=key)
            except modules.attribute.Attribute.DoesNotExist:
                pass
            else:
                self._attributes[key] = attribute

        if key not in self._attributes:
            raise ValueError(key)
        return self._attributes[key]

    def get_value(self, key):
        # Make sure attribute exists
        attribute = self.get_attribute(key)
        if attribute.key not in self._values and not self._populated:
            try:
                value = modules.attribute.Value.objects.get(
                    attribute=attribute, product=self._product)
            except modules.attribute.Value.DoesNotExist:
                pass
            else:
                self._values[attribute.key] = value
        
        # Create a new value if none found
        if attribute.key not in self._values:
            self._values[attribute.key] = modules.attribute.Value(
                product=self._product, attribute=attribute)
                
        return self._values[attribute.key]

    def get_value_value(self, key):
        return self.get_value(key).value

    def set_value_value(self, key, value):
        self.get_value(key).value = value

    def populate(self, values=None, attributes=None):
        if self._populated:
            return
        if values is None:
            values = self._product.values.all()
        self._populated = True
        if attributes:
            for attribute in attributes:
                self._attributes[attribute.key] = attribute
        for value in values:
            attribute = value.attribute
            self._attributes[attribute.key] = attribute
            if not self._values.has_key(attribute.key):
                self._values[attribute.key] = value

    def __getitem__(self, key):
        return self.get_value_value(key)

    def __setitem__(self, key, value):
        self.set_value_value(key, value)

    def __iter__(self):
        self.populate()
        for value in self._values.values():
            if not value.is_empty():
                yield value

    def __len__(self):
        count = 0
        for value in self:
            count += 1
        return count

    def save(self):
        for value in self._values.values():
            value.save_value()
