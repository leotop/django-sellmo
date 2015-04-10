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


from sellmo import modules, Module
from sellmo.api.decorators import view, chainable, link
from sellmo.api.configuration import define_setting
from sellmo.contrib.attribute.models import (Attribute,
                                                    Value,
                                                    ValueObject)
from sellmo.contrib.attribute.query import product_q

from django.http import Http404
from django.utils.translation import ugettext_lazy as _


class AttributeModule(Module):

    namespace = 'attribute'
    Attribute = Attribute
    Value = Value
    ValueObject = ValueObject
    
    attribute_types = {}
    
    value_format = define_setting(
        'VALUE_FORMAT',
        default=u"{value}")

    @chainable()
    def get_sorted_values(self, chain, values, attribute=None,
                          product=None, **kwargs):
        if chain:
            out = chain.execute(values=values, attribute=attribute,
                                product=product, **kwargs)
            values = out.get('values', values)
        return values

    @chainable()
    def get_sorted_attributes(self, chain, attributes, **kwargs):
        if chain:
            out = chain.execute(attributes=attributes, **kwargs)
            attributes = out.get('attributes', attributes)
        return attributes
    
    @link(namespace=modules.product.namespace, name='list')
    def list_products(self, request, products, **kwargs):
        keys = modules.attribute.Attribute.objects.all() \
                .values_list('key', flat=True)
        
        for key, value in request.GET.items():
            
            if key.startswith('attr__'):
                # Remove attr__ prefix
                key = key[len('attr__'):]
            elif key.split('__')[0] not in keys:
                continue
            
            parts = key.split('__')
            key = parts[0]
            operator = None
            if len(parts) == 2:
                # Operator found
                operator = parts[1]
            elif len(parts) > 2:
                # Invalid length, ignore
                continue
            
            products = self.filter(
                request=request, products=products, key=key, 
                value=value, operator=operator)
        
        return {
            'products': products
        }

    @chainable()
    def filter(self, chain, request, products, key, value, attribute=None,
               operator=None, **kwargs):
        
        if attribute is None:
            try:
                attribute = modules.attribute.Attribute.objects.get(key=key)
            except modules.attribute.Attribute.DoesNotExist:
                return products
        
        try:
            value = attribute.parse(value)
        except ValueError:
            return products
        
        if operator is None:
            q = product_q(attribute, value)
        else:
            qargs = {
                operator: value
            }
            q = product_q(attribute, **qargs)
        
        products = products.filter(q)
         
        if chain:
            out = chain.execute(
                request=request, products=products, key=key, value=value, 
                attribute=attribute, operator=operator, **kwargs)
            products = out.get('products', products)
        
        return products
        
    @classmethod
    def register_attribute_type(self, type, adapter, verbose_name=None):
        if verbose_name is None:
            verbose_name = unicode(type)
        self.attribute_types[type] = {
            'adapter': adapter,
            'verbose_name': verbose_name
        }