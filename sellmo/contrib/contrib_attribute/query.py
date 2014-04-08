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

from functools import wraps

#

from sellmo import modules

#

from django.db import models
from django.db.models import Q

#


class ValueQ(Q):

    def __init__(self, attribute, value=None, **kwargs):
        qargs = dict()
        qargs['attribute'] = attribute

        suffix = None
        if value is None:
            if len(kwargs) == 1:
                suffix, value = kwargs.popitem()

        if not value is None:
            value_field = attribute.value_field
            if not suffix is None:
                value_field = '%s__%s' % (value_field, suffix)
            qargs[value_field] = value

        super(ValueQ, self).__init__(**qargs)


class ProductQ(Q):

    pks = []

    def __init__(self, attribute=None, value=None, values=None, product_field='product', **kwargs):
        if not attribute is None:
            if values is None:
                # Query against all values provided by the manager
                values = modules.attribute.Value.objects.all()
            self.pks = values.filter(
                ValueQ(attribute, value, **kwargs)).values_list(product_field, flat=True).distinct()
            super(ProductQ, self).__init__(pk__in=self.pks)
        else:
            super(ProductQ, self).__init__()

    def clone(self):
        return Q(pk__in=self.pks)
