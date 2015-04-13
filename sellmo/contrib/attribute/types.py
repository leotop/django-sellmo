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


from django import forms
from django.db import models


class AttributeType(object):
    
    def __init__(self, key):
        self.key = key
        
    def get_value_field_name(self):
        return 'value_%s' % self.key
        
    def get_value_field(self):
        raise NotImplementedError()
    
    def parse(self, string):
        raise NotImplementedError()

    def get_choices(self):
        return None
        
    def get_model(self):
        return None
        
    def get_formfield_type(self):
        raise NotImplementedError()
        
    def is_empty(self, value):
        return value is None
    
    def get_verbose_name(self):
        return unicode(self.key)
        

class IntegerAttributeType(AttributeType):
    
    def __init__(self, key='int'):
        super(IntegerAttributeType, self).__init__(key)
    
    def get_value_field(self):
        return models.IntegerField(
            null=True,
            blank=True,
        )
        
    def get_formfield_type(self):
        return forms.IntegerField
        

class FloatAttributeType(AttributeType):
    
    def __init__(self, key='float'):
        super(FloatAttributeType, self).__init__(key)
    
    def get_value_field(self):
        return models.FloatField(
            null=True,
            blank=True,
        )
        
    def get_formfield_type(self):
        return forms.FloatField


class StringAttributeType(AttributeType):

    def __init__(self, key='string'):
        super(StringAttributeType, self).__init__(key)

    def get_value_field(self):
        return models.CharField(
            max_length=255,
            blank=True,
            default='',
        )
        
    def get_formfield_type(self):
        return forms.CharField
        
    def is_empty(self, value):
        return value is ''