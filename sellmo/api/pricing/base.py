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

from sellmo import modules
from sellmo.utils.formatting import call_or_format

#

from django.db import models
from decimal import Decimal

#

__all__ = [
    'Currency',
    'StampableProperty',
    'Price',
    'PriceType',
]

class Currency(object):
    """
    ISO 4217
    """        
    def __init__(self, code, name, format):
        self.code = code
        self.name = name
        self._format = format
        
    def __eq__(self, other):
        return self.code == other.code
        
    def __str__(self):
        return self.code
        
    def format(self, amount, align=-1):
        return call_or_format(self._format, amount=amount, align=align)
        
class PriceType(object):
    def __init__(self, key, name):
        self.key = key
        self.name = name
    
    def __str__(self):
        return self.key
        
class StampableProperty(object):

    def __init__(self, prop):
        self.prop = prop
        
    def __get__(self, obj, objtype):
        return modules.pricing.retrieve(stampable=obj, prop=self.prop)
    
    def __set__(self, obj, val):
        modules.pricing.stamp(stampable=obj, prop=self.prop, price=val)

class Price(object):
        
    @staticmethod
    def sanity_check(price, other):
        if not isinstance(price, Price) or not isinstance(other, Price):
            raise Exception("""Not a price""")
        if price.currency != other.currency:
            raise Exception("""Currency mismatch""")

    def __init__(self, amount=0, currency=None, type=None, context=None):
        if not isinstance(amount, Decimal):
            amount = Decimal(str(amount))
            
        if currency is None:
            currency = modules.pricing.get_currency()
        
        if currency is None:
            raise Exception("Could not resolve currency")
            
        if context is None:
            context = {}
        elif not isinstance(context, dict):
            raise Exception("Context should be a dict")
        
        self.amount = amount
        self.currency = currency
        self.type = str(type) if type else type
        self.context = context.copy()
        
        mutations = {}
        if self.type:
            mutations[self.type] = amount
        self.mutations = mutations
        
    def clone(self, cls=None, clone=None):
        if cls is None:
            cls = self.__class__
        price = cls(amount=self.amount, currency=self.currency, type=self.type, context=self.context)
        price.mutations = self.mutations.copy()
        return price
        
    def round(self, digits=2):
        price = self.clone()
        price.amount = Decimal(str(round(price.amount, digits)))
        price.mutations = {key : Decimal(str(round(amount, digits))) for key, amount in price.mutations.iteritems()}
        return price
        
    def _update_context(self, context):
        self.context.update(context)
        
    def _addition_mutations(self, mutations):
        for key, amount in mutations.iteritems():
            current = self.mutations.get(key, 0)
            self.mutations[key] = current + amount
        
    def __add__(self, other):
        Price.sanity_check(self, other)
        price = self.clone()
        price.amount += other.amount
        price._addition_mutations({key : amount for key, amount in other.mutations.iteritems()})
        price._update_context(other.context)
        return price
        
    def __sub__(self, other):
        Price.sanity_check(self, other)
        price = self.clone()
        price.amount -= other.amount
        price._addition_mutations({key : -amount for key, amount in other.mutations.iteritems()})
        price._update_context(other.context)
        return price
        
    def __mul__(self, multiplier):
        price = self.clone()
        price.amount *= multiplier
        price.mutations = {key : amount * multiplier for key, amount in price.mutations.iteritems()}
        return price
        
    def __div__(self, divider):
        price = self.clone()
        price.amount /= divider
        price.mutations = {key : amount / divider for key, amount in price.mutations.iteritems()}
        return price
        
    def __neg__(self):
        price = self.clone()
        price.amount = -price.amount
        price.mutations = {key : -amount for key, amount in price.mutations.iteritems()}
        return price
        
    def __contains__(self, key):
        if not isinstance(key, (basestring, PriceType)):
            raise TypeError()
        return self.mutations.has_key(str(key))
    
    def __getitem__(self, key):
        if not isinstance(key, (basestring, PriceType)):
            raise TypeError()
        key = str(key)
        if self.mutations.has_key(key):
            return Price(self.mutations[key], self.currency, key)
        raise KeyError(key)
        
    def __setitem__(self, key, value):
        if not isinstance(key, (basestring, PriceType)):
            raise TypeError()
        if not isinstance(value, Price):
            raise TypeError()
        self.mutations[str(key)] = value.amount
            
    def __nonzero__(self):
        return self.amount != 0
    
    def __unicode__(self):
        return self.currency.format(self.amount)
        
    def __repr__(self):
        return str(self.amount)
    