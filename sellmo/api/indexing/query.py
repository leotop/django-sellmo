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


from django.db.models.query import QuerySet

from sellmo.api.indexing.search import SQ, SearchQuery


def indexed_queryset_factory(queryset, index):
    if isinstance(queryset, IndexedQuerySet):
        raise Exception("This is already a different indexed queryset.")
    # Decide correct mro
    if issubclass(queryset.__class__, QuerySet):
        # We got a subclass of QuerySet
        # Subclass -> IndexedQuerySet -> QuerySet
        bases = (queryset.__class__, IndexedQuerySet)
    else:
        # We got a QuerySet
        bases = (IndexedQuerySet,)

    # Construct new QuerySet class and clone to this class
    indexed = queryset._clone(klass=type('IndexedQuerySet', bases, {}))
    indexed.index = index
    indexed.index_query = SearchQuery()
    return indexed


class IndexedQuerySet(QuerySet):

    def iterator(self):
        indexes = self.index.search(self.index_query)
        for row in super(IndexedQuerySet, self).iterator():
            yield row
            
    def _indexed_filter_or_exclude(self, negate, *args, **kwargs):
        clone = self._clone()
        if negate:
            clone.index_query.add_filter(~SQ(*args, **kwargs))
        else:
            clone.index_query.add_filter(SQ(*args, **kwargs))
        return clone
        
    def _clone(self, **kwargs):
        clone = super(IndexedQuerySet, self)._clone()
        clone.index = self.index
        clone.index_query = self.index_query.clone()
        return clone
    
    def indexed_filter(self, *args, **kwargs):
        return self._indexed_filter_or_exclude(False, *args, **kwargs)
        
    def indexed_exclude(self, *args, **kwargs):
        return self._indexed_filter_or_exclude(True, *args, **kwargs)
        
    def indexed_order_by(self, *args):
        clone = self._clone()
        clone.index_query.add_order_by(*args)
        return clone