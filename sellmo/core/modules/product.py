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

from django.http import Http404

#

import sellmo
from sellmo import modules
from sellmo.api.decorators import view, chainable
from sellmo.api.product.models import Product, ProductRelatable
from sellmo.api.http.query import QueryString

#


class ProductModule(sellmo.Module):

    namespace = 'product'
    prefix = 'products'
    Product = Product
    ProductRelatable = ProductRelatable
    subtypes = []
    reserved_url_params = ['sort']

    @classmethod
    def register_subtype(self, subtype):
        self.subtypes.append(subtype)

        # Shouldn't be a problem if Capital cased classnames are used.
        setattr(self, subtype.__name__, subtype)

    @chainable()
    def list(self, chain, request, products=None, query=None, **kwargs):
        if products is None:
            products = self.Product.objects.all()
        if query is None:
            query = QueryString(request)
        if chain:
            out = chain.execute(
                request=request, products=products, query=query, **kwargs)
            if out.has_key('products'):
                products = out['products']
        return products

    @chainable()
    def single(self, chain, request, products=None, **kwargs):
        if products is None:
            products = self.Product.objects.all()
        if chain:
            out = chain.execute(request=request, products=products, **kwargs)
            if out.has_key('products'):
                products = out['products']
        return products

    @view(r'^(?P<product_slug>[-a-zA-Z0-9_]+)$')
    def details(self, chain, request, product_slug, context=None, **kwargs):
        if context is None:
            context = {}
        try:
            product = self.single(
                request=request).polymorphic().get(slug=product_slug)
        except self.Product.DoesNotExist:
            raise Http404("""Product '%s' not found.""" % product_slug)

        if chain:
            return chain.execute(request, product=product, context=context, **kwargs)
        else:
            # We don't render anything
            raise Http404
