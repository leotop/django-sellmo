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

import operator

#

from django.http import Http404
from django.db.models import Q
from django.utils.module_loading import import_by_path

#

from sellmo import modules, Module
from sellmo.api.decorators import view, chainable
from sellmo.contrib.contrib_search.config import settings

#

class SearchModule(Module):
    namespace = 'search'
    
    def __init__(self, *args, **kwargs):
        self.SearchForm = import_by_path(settings.SEARCH_FORM)
        
    @chainable()
    def get_search_form(self, chain, form=None, cls=None, initial=None, data=None, **kwargs):
        if cls is None:
            cls = self.SearchForm
            
        if form is None:
            if not data and not initial:
                initial = {}
            
            if not data:
                form = cls(initial=initial)
            else:
                form = cls(data)
        
        if chain:
            out = chain.execute(form=form, cls=cls, initial=initial, data=data, **kwargs)
            out = out.get('form', form)
        return form

    @view(r'^$')
    def results(self, chain, request, products=None, context=None, **kwargs):
        if context is None:
            context = {}
        
        if products is None:
            products = modules.product.list(request=request)
        
        if chain:
            return chain.execute(request, products=products, context=context, **kwargs)
        else:
            # We don't render anything
            raise Http404
            
    @chainable()
    def search(self, chain, products, term, **kwargs):
        def construct_search(field):
            if field.startswith('^'):
                return "%s__istartswith" % field[1:]
            elif field.startswith('='):
                return "%s__iexact" % field[1:]
            elif field.startswith('@'):
                return "%s__search" % field[1:]
            else:
                return "%s__icontains" % field
        
        fields = settings.SEARCH_FIELDS
        if fields and term:
            orm_lookups = [construct_search(str(field)) for field in fields]
            for bit in term.split():
                or_queries = [Q(**{orm_lookup: bit})
                              for orm_lookup in orm_lookups]
                products = products.filter(reduce(operator.or_, or_queries))
            products = products.distinct()
        
        if chain:
            out = chain.execute(products=products, term=term, **kwargs)
            products = out.get('products', products)
        return products