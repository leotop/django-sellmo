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


import sellmo
from sellmo import modules, params
from sellmo.api.configuration import define_setting, define_import
from sellmo.api.indexing.exceptions import IndexMissingException

from django.utils import six


class IndexingModule(sellmo.Module):

    _registry = {}
    namespace = 'indexing'
    
    DefaultIndexAadapter = define_import(
        'DEFAULT_INDEX_ADAPTER',
        default='sellmo.api.indexing.adapters.database.DatabaseIndexAdapter')
        
    def __init__(self):
        # Initialize indexes
        self._indexes = {}
            
    def _initialize_index(self, index, name, adapter):
        adapter = adapter()
        
        instance = index(name, adapter)
        introspected_fields = adapter.introspect_index(instance)
        
        building = getattr(params, 'building_indexes', False)
        if introspected_fields is False:
            if building or adapter.supports_runtime_build():
                adapter.build_index(instance)
            else:
               raise IndexMissingException() 
        else:
            # Find simularies between introspected index
            # and current index
            intersection = {}
            added = {}
            deleted = {}
            
            all_fields = dict(introspected_fields, **instance.fields)
            for field_name, field in six.iteritems(all_fields):
                if (field_name in introspected_fields and
                        field_name in instance.fields):
                    intersection[field_name] = field
                elif field_name not in introspected_fields:
                    added[field_name] = field
                elif field_name not in instance.fields:
                    deleted[field_name] = field
                else:
                    # Field has changed, delete and add it
                    deleted[field_name] = field
                    added[field_name] = field
            
            if added or deleted:
                if (building or adapter.supports_runtime_build()):
                    adapter.rebuild_index(instance, added, deleted)
                else:
                    instance.fields = intersection
        
        adapter.initialize_index(instance)
        return instance
      
    def _reinitialize_index(self, index):
        instance = self._initialize_index(index.__class__, index.name, index.adapter)
        self._indexes[instance.name] = instance

    @classmethod
    def register_index(cls, name, index, adapter=None):
        if name in cls._registry:
            raise ValueError(name)
        cls._registry[name] = (index, adapter)
    
    def get_index(self, name):
        if name not in self._registry:
            raise KeyError(name)
        if name not in self._indexes:
            index, adapter = self._registry[name]
            if adapter is None:
                adapter = self.DefaultIndexAadapter
            instance = self._initialize_index(index, name, adapter)
            self._indexes[instance.name] = instance
        return self._indexes[name]
        
    def get_indexes(self):
        indexes = []
        for name in six.iterkeys(self._registry):
            indexes.append((name, self.get_index(name)))
        return indexes