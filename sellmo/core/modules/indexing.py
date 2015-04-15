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
from sellmo.api.decorators import chainable
from sellmo.api.configuration import define_setting, define_import
from sellmo.api.indexing.exceptions import IndexMissingException

from django.utils import six

import logging

logger = logging.getLogger('sellmo')


class IndexingModule(sellmo.Module):

    _registry = {}
    _indexes = {}
    namespace = 'indexing'
    
    DefaultIndexAdapter = define_import(
        'DEFAULT_INDEX_ADAPTER',
        default='sellmo.api.indexing.adapters.database.DatabaseIndexAdapter')
        
    @classmethod
    def register_index(self, name, index_cls, adapter_cls=None):
        if name in self._registry:
            raise ValueError(name)
        self._registry[name] = (index_cls, adapter_cls)
        
    def _invalidate_index(self, index):
        index = self.create_index(index.__class__, index.name, index.adapter)
        self._indexes[index.name] = index
            
    @chainable()
    def create_index(self, chain, index_cls, name, adapter, index=None, **kwargs):
        if index is None:
            index = index_cls(name, adapter)
        if chain:
            out = chain.execute(index_cls=index_cls, name=name,
                                index=index, adapter=adapter, **kwargs)
            index = out.get('index', index)
        
        introspected_fields = adapter.introspect_index(index)
        
        building = getattr(params, 'building_indexes', False)
        if introspected_fields is False:
            if building or adapter.supports_runtime_build():
                adapter.build_index(index)
            else:
               raise IndexMissingException() 
        else:
            # Find simularies between introspected index
            # and current index
            intersection = {}
            added = {}
            deleted = {}
            
            introspected_fields['document'] = index.fields['document']
            all_fields = dict(introspected_fields, **index.fields)
            
            for field_name, field in six.iteritems(all_fields):
                if (field_name in introspected_fields and
                        field_name in index.fields):
                        
                    # Both fields exists, compare them
                    a = introspected_fields[field_name]
                    b = index.fields[field_name]
                    if a == b:
                        intersection[field_name] = field
                        continue
                
                # Fields do not match
                if field_name not in introspected_fields:
                    added[field_name] = field
                elif field_name not in index.fields:
                    deleted[field_name] = field
                else:
                    # Field has changed, delete and add it
                    deleted[field_name] = field
                    added[field_name] = field
            
            if added or deleted:
                if (building or adapter.supports_runtime_build()):
                    adapter.rebuild_index(index, added, deleted)
                else:
                    logger.warning('Missing index fields')
                    print intersection
                    index.fields = intersection
        
        adapter.initialize_index(index)
        return index
    
    @chainable()
    def create_adapter(self, chain, adapter_cls, adapter=None, **kwargs):
        if adapter is None:
            adapter = adapter_cls()
        if chain:
            out = chain.execute(adapter_cls=adapter_cls, adapter=adapter, **kwargs)
            adapter = out.get('adapter', adapter)
        return adapter
    
    @chainable()
    def get_index(self, chain, name, index=None, **kwargs):
        if index is None:
            if name not in self._registry:
                raise KeyError(name)
            if name not in self._indexes:
                index_cls, adapter_cls = self._registry[name]
                if adapter_cls is None:
                    adapter_cls = self.DefaultIndexAdapter
                adapter = self.create_adapter(adapter_cls=adapter_cls)
                index = self.create_index(index_cls=index_cls, name=name, adapter=adapter)
                self._indexes[index.name] = index
            index = self._indexes[name]
        if chain:
            out = chain.execute(name=name, index=index, **kwargs)
            index = out.get('index', index)    
        return index
    
    @chainable()
    def get_indexes(self, chain, indexes=None, **kwargs):
        if indexes is None:
            indexes = {
                name: self.get_index(name=name)
                for name in six.iterkeys(self._registry)
            }
        if chain:
            out = chain.execute(indexes=indexes, **kwargs)
            indexes = out.get('indexes', indexes)
        return indexes