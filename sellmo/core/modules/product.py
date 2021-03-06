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


from django.http import Http404

import sellmo
from sellmo import modules
from sellmo.api.decorators import view, chainable, load
from sellmo.api.exceptions import ViewNotImplemented
from sellmo.api.product.models import Product, ProductRelatable
from sellmo.api.product.indexes import ProductIndex
from sellmo.api.http.query import QueryString


@load(action='finalize_product_Product')
def finalize_model():
    class Product(modules.product.Product):

        class Meta(modules.product.Product.Meta):
            app_label = 'product'

    modules.product.Product = Product


@load(action='finalize_product_ProductIndex')
@load(after='finalize_product_Product')
def register_index():
    
    class ProductIndex(modules.product.ProductIndex):
        model = modules.product.Product
        
    modules.product.ProductIndex = ProductIndex
    modules.indexing.register_index('product', ProductIndex)
     

class ProductModule(sellmo.Module):

    namespace = 'product'
    Product = Product
    ProductRelatable = ProductRelatable
    subtypes = []
    reserved_url_params = ['sort']
    
    ProductIndex = ProductIndex

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
        
        index = modules.indexing.get_index(name='product')
        products = index.get_indexed_queryset(products)
        
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

    @view(r'^(?P<product_slug>[-a-zA-Z0-9_]+)/$')
    def product(self, chain, request, product_slug, product=None,
                context=None, **kwargs):
        
        if context is None:
            context = {}
            
        if product is None:
            try:
                product = self.single(request=request).polymorphic() \
                              .get(slug=product_slug)
            except self.Product.DoesNotExist:
                raise Http404("Product '{0}' not found.".format(product_slug))
        
        if chain:
            return chain.execute(request=request, product_slug=product_slug,
                                 product=product, context=context, **kwargs)
        else:
            raise ViewNotImplemented
