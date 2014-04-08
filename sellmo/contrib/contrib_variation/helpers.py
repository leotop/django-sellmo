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
from sellmo.contrib.contrib_attribute.helpers import AttributeHelper as AttributeHelperBase

#

from django.db import models
from django.core.exceptions import ValidationError
from django.utils.translation import ugettext_lazy as _
from django.utils.encoding import smart_text
from django.utils.text import capfirst

#


class AttributeHelper(AttributeHelperBase):

    def populate(self):
        if self.__dict__['_populated']:
            return
        self.__dict__['_populated'] = True
        for value in modules.attribute.Value.objects.filter(product=self._product, variates=False):
            attribute = value.attribute
            self._attributes[attribute.key] = attribute
            if not self._values.has_key(attribute.key):
                self._values[attribute.key] = value

    def get_value(self, key):
        attribute = self.get_attribute(key)
        if not self._values.has_key(attribute.key):
            try:
                value = modules.attribute.Value.objects.get(
                    attribute=attribute, product=self._product, variates=False)
            except modules.attribute.Value.DoesNotExist:
                self._values[attribute.key] = modules.attribute.Value(
                    product=self._product, attribute=attribute)
            else:
                self._values[attribute.key] = value
        return self._values[attribute.key]


class VariantAttributeHelper(AttributeHelper):

    def get_value_value(self, key):
        value = self.get_value(key)
        if not value.is_assigned:
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
            if value.is_assigned:
                yield value


class VariationAttributeHelper(object):

    def __init__(self, variation):
        self._variation = variation
        self._variant = variation.variant.downcast()

    def __iter__(self):
        values = {}
        for value in self._variation.values.all():
            values[value.attribute.key] = value
        for value in self._variant.attributes:
            if value.attribute.key not in values:
                values[value.attribute.key] = value
        for value in values.values():
            if value.is_assigned:
                yield value
