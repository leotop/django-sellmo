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


import logging
import copy
import itertools
from collections import OrderedDict

from django.utils import six
from django.db import models

from sellmo import modules
from sellmo.api.indexing.fields import IndexField, ModelField
from sellmo.api.indexing.exceptions import IndexInvalidatedException, IndexFieldException
from sellmo.api.indexing.query import indexed_queryset_factory


logger = logging.getLogger('sellmo')


class IndexMetaClass(type):

    def __new__(mcs, name, bases, attrs):
        
        # Collect fields from current class.
        current_fields = []
        for key, value in list(attrs.items()):
            if isinstance(value, IndexField):
                current_fields.append((key, value))
                attrs.pop(key)
        current_fields.sort(key=lambda x: x[1].creation_counter)
        attrs['declared_fields'] = OrderedDict(current_fields)
        
        new_class = (super(IndexMetaClass, mcs)
            .__new__(mcs, name, bases, attrs))
            
        if bases == (object,):
            return new_class
        
        # Walk through the MRO.
        declared_fields = OrderedDict()
        for base in reversed(new_class.__mro__):
            # Collect fields from base class.
            if hasattr(base, 'declared_fields'):
                declared_fields.update(base.declared_fields)
        
            # Field shadowing.
            for attr, value in base.__dict__.items():
                if value is None and attr in declared_fields:
                    declared_fields.pop(attr)
                    
        model = getattr(new_class, 'model', None)
        if model:
            if not issubclass(model, models.Model):
                raise ValueError('Index model %s is not a model.' % model)
            # Create document field
            declared_fields['document'] = ModelField(
                model,
                required=True,
                populate_value_cb=(lambda document, **variety: document))
        
        new_class.base_fields = declared_fields
        new_class.declared_fields = declared_fields
        
        return new_class
        
        
class Index(six.with_metaclass(IndexMetaClass, object)):
    
    model = None
    
    # Will be the intersection of original and introspected fields
    # and shall only be used.
    fields = None
    
    # Handy for adapter
    original_fields = None
    introspected_fields = None
    difference = None
    
    _invalidated = False
    
    def __init__(self, name, adapter):
        if self.model is None:
            raise ValueError("Index has no model class specified.")
        self.name = name
        self.adapter = adapter
        self.fields = self.get_fields()
        
    def get_fields(self):
        return copy.deepcopy(self.base_fields)
        
    def populate(self, document, values, **variety):
        return values
        
    def build_records(self, document):
        # Create all possible varieties
        varieties = itertools.product(*[
            [(field_name, variety) for variety in field.varieties] 
            for field_name, field in six.iteritems(self.fields)
            if field.varieties
        ])
        
        results = []
        for variety in  varieties:
            
            # Unpack to dict
            variety = { key: value for key, value in variety }
            
            values = {}
            missing = {}
            
            # First get values from each seperate field
            for field_name, field in six.iteritems(self.fields):
                if field_name in variety:
                    values[field_name] = variety[field_name]
                else:
                    has_value, value = field.populate_field(document, **variety)
                    if has_value:
                        values[field_name] = value
                    else:
                        missing[field_name] = field
            
            # Now allow index to provide additonal values
            result = {}
            for field_name, value in six.iteritems(self.populate(document, values, **variety)):
                if field_name not in self.fields:
                    logger.info("Value %s for field %s will be omitted from index" % (value, field_name))
                    continue
                missing.pop(field_name, None)
                result[field_name] = value
            
            for field_name, field in six.iteritems(missing):
                if field.required:
                    raise IndexFieldException("%s is required" % field_name)
                    
            results.append(result)
        
        return results
        
    def _not_invalidated(self):
        if self._invalidated:
            raise IndexInvalidatedException()
    
    def get_queryset(self, queryset=None):
        if queryset is None:
            queryset = self.model.objects.all()
        elif not (queryset.model == self.model or 
                issubclass(queryset.model, self.model)):
            raise ValueError("Invalid QuerySet")
        return queryset
        
    def invalidate(self):
        modules.indexing._invalidate_index(self)
        self._invalidated = True
        
    def search(self, query):
        self._not_invalidated()
        return self.adapter.search_index(self, query)
        
    def update(self, queryset=None):
        self._not_invalidated()
        self.adapter.update_index(self, self.get_queryset(queryset))
        
    def clear(self, queryset=None):
        self._not_invalidated()
        self.adapter.clear_index(self, self.get_queryset(queryset))
        
    def get_indexed_queryset(self, queryset=None):
        self._not_invalidated()
        return indexed_queryset_factory(self.get_queryset(queryset), self)