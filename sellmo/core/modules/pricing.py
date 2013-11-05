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

from django.db import models
from decimal import Decimal

#

import sellmo
from sellmo import modules
from sellmo.api.decorators import view, chainable, load
from sellmo.api.pricing import Price, StampableProperty

#

def get_default_currency():
    return modules.pricing.get_currency().code

class PricingModule(sellmo.Module):
    """
    Routes product pricing logic to higher level modules and acts as a container for pricing
    related models.
    """
    namespace = 'pricing'
    currency = None
    types = []
    
    #: Configures the max digits for a pricing (decimal) field
    decimal_max_digits = 9
    #: Configures the amount of decimal places for a pricing (decimal) field
    decimal_places = 2
    
    
    @chainable()
    def construct_decimal_field(self, chain, **kwargs):
        """
        Constructs a decimal field.
        """
        return models.DecimalField(
            max_digits = modules.pricing.decimal_max_digits,
            decimal_places = modules.pricing.decimal_places,
            **kwargs
        )
        
    @chainable()
    def construct_pricing_field(self, chain, **kwargs):
        """
        Constructs a pricing (decimal) field.
        """
        if not kwargs.has_key('default'):
            kwargs['default'] = Decimal('0.0')
        return self.construct_decimal_field(**kwargs)
        
    @chainable()
    def construct_currency_field(self, chain, **kwargs):
        """
        Constructs a currency field.
        """
        return models.CharField(
            max_length = 3,
            default = get_default_currency
        )
        
    @chainable()
    def make_stampable(self, chain, cls, properties, **kwargs):
        
        class Meta:
            abstract = True
        
        name = cls.__name__
        attr_dict = {
            'Meta' : Meta,
            '__module__' : cls.__module__
        }
        
        for prop in properties:
            attr_dict[prop] = StampableProperty(prop)
            attr_dict['{0}_currency'.format(prop)] = self.construct_currency_field()
            fields = ['{0}_{1}'.format(prop, field) for field in self.types + ['amount']]
            for field in fields:
                attr_dict[field] = self.construct_pricing_field()
            
        model = type(name, (cls,), attr_dict)
        return model
        
    @chainable()
    def retrieve(self, chain, stampable, prop, **kwargs):
        fields = ['{0}_{1}'.format(prop, field) for field in self.types]
        price = Price(getattr(stampable, '{0}_amount'.format(prop)))
        for field in self.types:
            price[field] = Price(getattr(stampable, '{0}_{1}'.format(prop, field)))
        return price
            
    @chainable()
    def stamp(self, chain, stampable, prop, price, **kwargs):
        setattr(stampable, '{0}_amount'.format(prop), price.amount)
        setattr(stampable, '{0}_currency'.format(prop), price.currency.code)
        for field in self.types:
            if field in price:
                amount = price[field].amount
            else:
                amount = Decimal(0.0)
            setattr(stampable, '{0}_{1}'.format(prop, field), amount)
        
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
    def get_price(self, chain, currency=None, price=None, **kwargs):
        if currency is None:
            currency = self.get_currency()
        if price is None:
            price = Price(0, currency=currency)
        if chain:
            out = chain.execute(price=price, currency=currency, **kwargs)
            if out.has_key('price'):
                price = out['price']
        
        return price
    