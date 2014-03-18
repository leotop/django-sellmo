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

import logging
from decimal import Decimal
import types

#

from django.db import models
from django.utils.translation import ugettext_lazy as _, string_concat

#

import sellmo
from sellmo import modules
from sellmo.config import settings
from sellmo.api.decorators import view, chainable, link
from sellmo.api.pricing import Currency, Price, PriceType, StampableProperty
from sellmo.api.pricing.index import PriceIndex, PrefetchedPriceIndex
from sellmo.api.pricing.models import PriceIndexBase

#

logger = logging.getLogger('sellmo')

#

def get_default_currency():
    return str(modules.pricing.get_currency())

class PricingModule(sellmo.Module):
    """
    Routes pricing logic to higher level modules.
    """
    namespace = 'pricing'
    currency = None
    currencies = {}
    types = []
    indexes = {}
    
    PriceIndexBase = PriceIndexBase
    
    #: Configures the max digits for a pricing (decimal) field
    decimal_max_digits = 9
    #: Configures the amount of decimal places for a pricing (decimal) field
    decimal_places = 2
    
    def __init__(self, *args, **kwargs):
        # Configure
        if self.currency is None:
            self.currency = Currency(*settings.CURRENCY)
        if not self.currencies:
            self.currencies = {
                self.currency.code : self.currency
            }
        
        # Initialize indexes
        for index in self.indexes.values():
            index.add_kwarg(
                'currency',
                field_name='price_currency',
                transform=lambda value : value.code,
                default=self.currencies.values()
            )
            index._build()
            self.register(index.model.__name__, index.model)
    
    @classmethod
    def construct_decimal_field(self, **kwargs):
        """
        Constructs a decimal field.
        """
        return models.DecimalField(
            max_digits = modules.pricing.decimal_max_digits,
            decimal_places = modules.pricing.decimal_places,
            **kwargs
        )
        
    @classmethod
    def construct_pricing_field(self, **kwargs):
        """
        Constructs a pricing (decimal) field.
        """
        if not kwargs.has_key('default'):
            kwargs['default'] = Decimal('0.0')
        return self.construct_decimal_field(**kwargs)
        
    @classmethod
    def construct_currency_field(self, **kwargs):
        """
        Constructs a currency field.
        """
        choices = [(currency.code, currency.name) for currency in self.currencies]
        return models.CharField(
            max_length = 3,
            default = get_default_currency,
            choices = choices,
            **kwargs
        )
        
    @classmethod
    def make_stampable(self, model, properties, **kwargs):
        
        class Meta(model.Meta):
            abstract = True
        
        name = model.__name__
        attr_dict = {
            'Meta' : Meta,
            '__module__' : model.__module__
        }
        
        for prop in properties:
            verbose_name = None
            if isinstance(prop, (types.ListType, types.TupleType)):
                if len(prop) > 1:
                    verbose_name = prop[1]
                prop = prop[0]
            
            #
            attr_dict[prop] = StampableProperty(prop)
            
            # Construct price currency field
            fargs = {}
            if verbose_name:
                fargs['verbose_name'] = string_concat(verbose_name, ' ', _("currency"))
            else:
                fargs['verbose_name'] = _("currency")
            
            attr_dict['{0}_currency'.format(prop)] = self.construct_currency_field(**fargs)
            
            # Construct price type fields (including the standard amount field)
            for key in self.types + ['amount']:
                field = '{0}_{1}'.format(prop, key)
                fargs = {}
                
                if key == 'amount':
                    fargs['verbose_name'] = verbose_name  
                elif hasattr(key, 'name'):
                    if verbose_name:
                        fargs['verbose_name'] = string_concat(verbose_name, ' ', key.name)
                    else:
                        fargs['verbose_name'] = key.name
                    
                attr_dict[field] = self.construct_pricing_field(**fargs)
            
        out = type(name, (model,), attr_dict)
        return out
        
    @classmethod
    def create_index(self, identifier):
        if identifier in self.indexes:
            raise Exception("Index '{0}' already exists.".format(identifier))
        index = PriceIndex(identifier)
        self.indexes[identifier] = index
        return index
        
    @classmethod
    def get_index(self, identifier):
        if identifier not in self.indexes:
            raise Exception("Index '{0}' not found.".format(identifier))
        return self.indexes[identifier]
    
    @chainable()
    def update_index(self, chain, index, invalidations, **kwargs):
        
        # Collect index kwargs
        out = {}
        if chain:
            out.update(chain.execute(index=index, invalidations=invalidations, **kwargs))
            
        # Filter out kwargs
        kwargs = { key : value for key, value in out.iteritems() if index.is_kwarg(key)}
            
        # Get actual index
        index = self.get_index(index)
            
        # Now invalidate
        logger.info("Invalidating {1} indexes for index '{0}'".format(index, invalidations.count()))
        invalidations.invalidate()
        
        # Create and index all combinations
        def do(remaining, combination=None):
            if combination is None:
                combination = {}
            if remaining:
                key, values = remaining.popitem()
                for value in values:
                    merged = {key : value}
                    merged.update(combination)
                    do(dict(remaining), merged)
            else:
                index.index(self.get_price(**combination), **combination)
        do(kwargs)
        
    @chainable()
    def retrieve(self, chain, stampable, prop, price=None, **kwargs):
        if price is None:
            amount = getattr(stampable, '{0}_amount'.format(prop))
            currency = getattr(stampable, '{0}_currency'.format(prop))
            price = Price(amount, currency=self.currencies[currency])
            for key in self.types:
                price[key] = Price(getattr(stampable, '{0}_{1}'.format(prop, key)))
        if chain:
            out = chain.execute(stampable=stampable, prop=prop, price=price, **kwargs)
            price = out.get('price', price)
        return price
            
    @chainable()
    def stamp(self, chain, stampable, prop, price, **kwargs):
        setattr(stampable, '{0}_amount'.format(prop), price.amount)
        setattr(stampable, '{0}_currency'.format(prop), price.currency.code )
        for key in self.types:
            if key in price:
                amount = price[key].amount
            else:
                amount = Decimal(0.0)
            setattr(stampable, '{0}_{1}'.format(prop, key), amount)
        if chain:
            chain.execute(stampable=stampable, prop=prop, price=price, **kwargs)
        
    @chainable()
    def get_currency(self, chain, request=None, currency=None, **kwargs):
        if currency is None:
            currency = self.currency
        if chain:
            out = chain.execute(request=request, currency=currency, **kwargs)
            if out.has_key('currency'):
                currency = out['currency']
        return currency
            
    @chainable()
    def get_price(self, chain, currency=None, price=None, index=None, **kwargs):
        if currency is None:
            currency = self.get_currency()
        
        # Price indexing
        if index:
            if isinstance(index, PrefetchedPriceIndex):
                price = index.lookup(currency=currency.code, **kwargs)
            else:
                price = self.get_index(index).lookup(currency=currency, **kwargs)
            if price is not None:
                return price
            
        if price is None:
            price = Price(0, currency=currency)
        if chain:
            out = chain.execute(price=price, currency=currency, **kwargs)
            if out.has_key('price'):
                price = out['price']
        
        # Price indexing
        if index and not isinstance(index, PrefetchedPriceIndex):
            self.get_index(index).index(price, currency=currency, **kwargs)
        
        return price
        
    @link(namespace='product', name='list')
    def list_products(self, products, query=None, currency=None, index=None, index_relation='product', **kwargs):
        if currency is None:
            currency = self.get_currency()
        if index is not None:
            products = self.get_index(index).query(products, index_relation, currency=currency, **kwargs)
        if query is not None:
            # See if we need to sort on price
            if ('sort', 'price') in query:
                products = products.order_indexes_by('price_amount')
            elif ('sort', '-price') in query:
                products = products.order_indexes_by('-price_amount')
                
        return {
            'products' : products
        }