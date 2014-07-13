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


from functools import wraps

from sellmo import modules

from django.db import models
from django.db.models import Q
from django.utils import six


def value_q(attribute, *args, **kwargs):
    if not isinstance(attribute, modules.attribute.Attribute):
        raise ValueError("attribute must be an instance of Attribute")
    qargs = dict()
    qargs['attribute'] = attribute

    for operator, value in kwargs.iteritems():
        # Apply operator
        lookup = '{0}__{1}'.format(attribute.value_field, operator)
        qargs[lookup] = value
        
    for value in args:
        lookup = attribute.value_field
        qargs[lookup] = value
    
    return Q(**qargs)


def product_q(attribute, *args, **kwargs):
    if not isinstance(attribute, modules.attribute.Attribute):
        raise ValueError("attribute must be an instance of Attribute")
         
    values = kwargs.pop('values', modules.attribute.Value.objects.all())
    through = kwargs.pop('through', 'values')
    
    qargs = {
        '{0}__in'.format(through): values.filter(
            value_q(attribute, *args, **kwargs))
    }
    
    return Q(**qargs)
