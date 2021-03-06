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


from sellmo import modules
from sellmo.api import indexing

from django.utils import six


class PriceIndex(indexing.Index):
    
    price_prefixes = []
    
    def populate(self, document, values, **variety):
        values = super(PriceIndex, self).populate(document, values, **variety)
        kwargs = self.get_price_kwargs(document, **variety)
        
        currencies = modules.pricing.currencies
        types = modules.pricing.types
        
        for prefix in self.price_prefixes:
            for currency_code, currency in six.iteritems(currencies):
                price = self.get_price(document, prefix, currency_code, currency, **kwargs)
                if price:
                    for key in types + ['amount']:
                        field_name = '%s_%s_%s' % (prefix, currency_code, key)
                        amount = None
                        if key == 'amount':
                            amount = price.amount
                        elif key in price:
                            amount = price[key].amount
                        values[field_name] = amount
        return values
        
    def get_price_kwargs(self, document, **variety):
        return {}
        
    def get_price(self, document, prefix, currency_code, currency, **kwargs):
        raise NotImplementedError()
    
    def get_fields(self):
        fields = super(PriceIndex, self).get_fields()
        
        currencies = modules.pricing.currencies
        types = modules.pricing.types
        
        for prefix in self.price_prefixes:
            for currency_code, currency in six.iteritems(currencies):
                for key in types + ['amount']:
                    field_name = '%s_%s_%s' % (prefix, currency_code, key)
                    fields[field_name] = indexing.DecimalField(
                        max_digits=modules.pricing.decimal_max_digits,
                        decimal_places=modules.pricing.decimal_places)
                    
                    extra_fields = getattr(key, 'extra_fields', {})
                    for extra_field_name, extra_field in extra_fields.iteritems():
                        name = '%s_%s'.format(field_name, extra_field_name)
                
        return fields