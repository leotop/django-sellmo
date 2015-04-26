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


class IndexField(object):
    
    required = False
    creation_counter = 0
    
    def __init__(self, populate_value_cb=None,
                    varieties=None, **kwargs):
        self.populate_value_cb = populate_value_cb
        self.varieties = varieties
        self.required = varieties is not None
        if 'default' in kwargs:
            self.default = kwargs['default']
        if 'required' in kwargs:
            required = kwargs['required']
            if varieties is not None and not required:
                raise ValueError("Fields who provide varieties"
                                 " are always required.")
            self.required = required
        
    def populate_field(self, document, **variety):
        if self.populate_value_cb is not None:
            return (True, self.populate_value_cb(document, **variety))
        elif hasattr(self, 'default'):
            return (True, self.default)
        return (False, None)
        
    def __eq__(self, other):
        return (type(self) is type(other)
                and (self.required == other.required
                        or self.required is None
                        or other.required is None))
                
    def __repr__(self):
        path = '%s.%s' % (self.__class__.__module__, self.__class__.__name__)
        return '<%s>' % path
    

class ModelField(IndexField):
    
    def __init__(self, model, *args, **kwargs):
        super(ModelField, self).__init__(*args, **kwargs)
        self.model = model
        
    def __eq__(self, other):
        return (super(ModelField, self).__eq__(other)
                and self.model is other.model)
    
    
class BooleanField(IndexField):
    pass
    
    
class CharField(IndexField):
    
    def __init__(self, max_length, *args, **kwargs):
        super(CharField, self).__init__(*args, **kwargs)
        self.max_length = max_length
        
    def __eq__(self, other):
        return (super(ModelField, self).__eq__(other)
                and self.max_length == other.max_length)
    
    
class IntegerField(IndexField):
    pass
    
    
class FloatField(IndexField):
    pass
    
    
class DecimalField(IndexField):
    
    def __init__(self, max_digits, decimal_places, *args, **kwargs):
        super(DecimalField, self).__init__(*args, **kwargs)
        self.max_digits = max_digits
        self.decimal_places = decimal_places
        
    def __eq__(self, other):
        return (super(DecimalField, self).__eq__(other)
                and (self.max_digits == other.max_digits
                        or self.max_digits is None
                        or other.max_digits is None)
                and (self.decimal_places == other.decimal_places
                        or self.decimal_places is None
                        or other.max_digits is None))