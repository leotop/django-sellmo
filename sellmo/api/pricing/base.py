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

#

from django.db import models
from decimal import Decimal

class Currency(object):
    
    """
    ISO 4217
    """
    def __init__(self, code, description, format):
        self.code = code
        self.description = description
        self._format = format
        
    def format(self, amount):
        return self._format.format(amount=amount)

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
        self.type = type
        self.context = context.copy()
        
        mutations = {}
        if type:
            mutations[type] = amount
        self.mutations = mutations
        
    def clone(self, cls=None):
        if cls is None:
            cls = self.__class__
        price = cls(amount=self.amount, currency=self.currency, type=self.type, context=self.context)
        price.mutations = self.mutations.copy()
        return price
        
    def _update_context(self, context):
        self.context.update(context)
        
    def _addition_mutations(self, mutations):
        for type, amount in mutations.iteritems():
            current = self.mutations.get(type, 0)
            self.mutations[type] = current + amount
        
    def __invert__(self):
        price = self.clone()
        price.amount = -price.amount
        price.mutations = {type : -amount for type, amount in price.mutations.iteritems()}
        return price
        
    def __add__(self, other):
        Price.sanity_check(self, other)
        price = self.clone()
        price.amount += other.amount
        price._addition_mutations({type : amount for type, amount in other.mutations.iteritems()})
        price._update_context(other.context)
        return price
        
    def __sub__(self, other):
        Price.sanity_check(self, other)
        price = self.clone()
        price.amount -= other.amount
        price._addition_mutations({type : -amount for type, amount in other.mutations.iteritems()})
        price._update_context(other.context)
        return price
        
    def __mul__(self, multiplier):
        price = self.clone()
        price.amount *= multiplier
        price.mutations = {type : amount * multiplier for type, amount in price.mutations.iteritems()}
        return price
        
    def __div__(self, divider):
        price = self.clone()
        price.amount /= multiplier
        price.mutations = {type : amount / multiplier for type, amount in price.mutations.iteritems()}
        return price
        
    def __contains__(self, key):
        if not isinstance(key, basestring):
            raise TypeError()
        return self.mutations.has_key(key)
    
    def __getitem__(self, key):
        if not isinstance(key, basestring):
            raise TypeError()
        if self.mutations.has_key(key):
            return Price(self.mutations[key], self.currency, key)
        raise KeyError(key)
        
    def __setitem__(self, key, value):
        if not isinstance(key, basestring):
            raise TypeError()
        if not isinstance(value, Price):
            raise TypeError()
        if key:
            self.mutations[key] = value.amount
        else:
            raise KeyError(key)
            
    def __nonzero__(self):
        return self.amount > 0
    
    def __unicode__(self):
        return self.currency.format(self.amount)
    