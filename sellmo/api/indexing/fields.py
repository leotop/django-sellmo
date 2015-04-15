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
    
    creation_counter = 0
    
    def __init__(self, populate_value_cb=None, required=False,
                    varieties=None, **kwargs):
        self.populate_value_cb = populate_value_cb
        self.required = required
        self.varieties = varieties
        if 'default' in kwargs:
            self.default = kwargs['default']
        
    def populate_field(self, document, **variety):
        if self.populate_value_cb is not None:
            return (True, self.populate_value_cb(document, **variety))
        elif hasattr(self, 'default'):
            return (True, self.default)
        return (False, None)
        
    def __eq__(self, other):
        return type(self) is type(other)
    

class ModelField(IndexField):
    
    def __init__(self, model, *args, **kwargs):
        super(ModelField, self).__init__(*args, **kwargs)
        self.model = model
        
    def __eq__(self, other):
        return (super(ModelField, self).__eq__(other)
                and self.model is other.model)
        
class DocumentField(ModelField):
    
    def __init__(self, model):
        super(DocumentField, self).__init__(model, required=True)
        
    def populate_field(self, document, **variety):
        return True, document
    
    
class BooleanField(IndexField):
    pass
    
    
class CharField(IndexField):
    
    def __init__(self, max_length, *args, **kwargs):
        super(CharField, self).__init__(*args, **kwargs)
        self.max_length = max_length
    
    
class IntegerField(IndexField):
    pass
    
    
class FloatField(IndexField):
    pass
    
    
class DecimalField(IndexField):
    
    def __init__(self, max_digits, decimal_places, *args, **kwargs):
        super(DecimalField, self).__init__(*args, **kwargs)
        self.max_digits = max_digits
        self.decimal_places = decimal_places