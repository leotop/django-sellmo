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
from sellmo.contrib.contrib_attribute.helpers import AttributeHelper

#

from django.db import models
from django.core.exceptions import ValidationError
from django.utils.translation import ugettext_lazy as _
from django.utils.encoding import smart_text
from django.utils.text import capfirst

#

class RecipelessAttributeHelper(AttributeHelper):
    
    def populate(self):
        if self.__dict__['_populated']:
            return
        self.__dict__['_populated'] = True
        for value in modules.attribute.Value.objects.filter(product=self._product, recipe__isnull=True):
            attribute = value.attribute
            self._attributes[attribute.key] = attribute
            if not self._values.has_key(attribute.key):
                self._values[attribute.key] = value

    def get_value(self, key):
        attribute = self.get_attribute(key)
        if not self._values.has_key(attribute.key):
            try:
                value = modules.attribute.Value.objects.get(attribute=attribute, product=self._product, recipe__isnull=True)
            except modules.attribute.Value.DoesNotExist:
                self._values[attribute.key] = modules.attribute.Value(product=self._product, attribute=attribute)
            else:
                self._values[attribute.key] = value
        return self._values[attribute.key]