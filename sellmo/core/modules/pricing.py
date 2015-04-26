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


import logging
import types
from decimal import Decimal

from django.db import models
from django.utils.translation import ugettext_lazy as _, string_concat

import sellmo
from sellmo import modules
from sellmo.api.decorators import view, chainable, link
from sellmo.api.configuration import define_setting, define_import
from sellmo.api.pricing import Currency, Price, PriceType, StampableProperty


def get_default_currency():
    return str(modules.pricing.get_currency())


RESERVED_NAMES = ['amount', 'currency']


class PricingModule(sellmo.Module):

    """
    Routes pricing logic to higher level modules.
    """
    namespace = 'pricing'
    
    types = []
    
    default_currency = define_setting(
        'DEFAULT_CURRENCY',
        default=('eur', _(u"euro"), _(u"\u20ac {amount:\u00a0>{align}.2f}")),
        transform=lambda value : Currency(*value)
    )
    
    currencies = define_setting(
        'CURRENCIES',
        required=False,
        default={}
    )

    #: Configures the max digits for a pricing (decimal) field
    decimal_max_digits = define_setting(
        'DECIMAL_MAX_DIGITS',
        default=9
    )
    #: Configures the amount of decimal places for a pricing (decimal) field
    decimal_places = define_setting(
        'DECIMAL_PLACES',
        default=2
    )

    def __init__(self, *args, **kwargs):
        # Configure
        if not self.currencies:
            self.currencies = {
                self.default_currency.code: self.default_currency
            }
        for name in RESERVED_NAMES:
            assert name not in self.types, "%s is a reserved name" % name

    @classmethod
    def construct_decimal_field(self, **kwargs):
        """
        Constructs a decimal field.
        """
        return models.DecimalField(
            max_digits=modules.pricing.decimal_max_digits,
            decimal_places=modules.pricing.decimal_places,
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
        choices = [(currency.code, currency.name)
                   for currency in self.currencies]
        return models.CharField(
            max_length=3,
            default=get_default_currency,
            choices=choices,
            **kwargs
        )

    @classmethod
    def make_stampable(self, model, properties, **kwargs):

        class Meta(model.Meta):
            abstract = True

        name = model.__name__
        attr_dict = {
            'Meta': Meta,
            '__module__': model.__module__
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
                fargs['verbose_name'] = string_concat(
                    verbose_name, ' ', _("currency"))
            else:
                fargs['verbose_name'] = _("currency")

            field = '{0}_currency'.format(prop) 
            attr_dict[field] = self.construct_currency_field(**fargs)

            # Construct price type fields
            # (including the standard amount field)
            for key in self.types + ['amount']:
                field = '{0}_{1}'.format(prop, key)
                fargs = {}

                if key == 'amount':
                    fargs['verbose_name'] = verbose_name
                elif hasattr(key, 'name'):
                    if verbose_name:
                        fargs['verbose_name'] = string_concat(
                            verbose_name, ' ', key.name)
                    else:
                        fargs['verbose_name'] = key.name
                
                attr_dict[field] = self.construct_pricing_field(**fargs)
                
                extra_fields = getattr(key, 'extra_fields', {})
                for extra_field_name, extra_field in extra_fields.iteritems():
                    name = '{0}_{1}'.format(field, extra_field_name)
                    attr_dict[name] = extra_field[0](
                        *extra_field[1], **extra_field[2])

        out = type(name, (model,), attr_dict)
        return out

    @chainable()
    def retrieve(self, chain, stampable, prop, price=None, **kwargs):
        if price is None:
            amount = getattr(stampable, '{0}_amount'.format(prop))
            currency = getattr(stampable, '{0}_currency'.format(prop))
            price = Price(amount, currency=self.currencies[currency])
            for key in self.types:
                price[key] = Price(
                    getattr(stampable, '{0}_{1}'.format(prop, key)))
        if chain:
            out = chain.execute(
                stampable=stampable, prop=prop, price=price, **kwargs)
            price = out.get('price', price)
        return price

    @chainable()
    def stamp(self, chain, stampable, prop, price, **kwargs):
        setattr(stampable, '{0}_amount'.format(prop), price.amount)
        setattr(stampable, '{0}_currency'.format(prop), price.currency.code)
        for key in self.types:
            if key in price:
                amount = price[key].amount
            else:
                amount = Decimal(0.0)
            setattr(stampable, '{0}_{1}'.format(prop, key), amount)
        if chain:
            chain.execute(
                stampable=stampable, prop=prop, price=price, **kwargs)

    @chainable()
    def get_currency(self, chain, request=None, currency=None, **kwargs):
        if currency is None:
            currency = self.default_currency
        if chain:
            out = chain.execute(request=request, currency=currency, **kwargs)
            if out.has_key('currency'):
                currency = out['currency']
        return currency

    @chainable()
    def get_price(self, chain, currency=None, price=None, index=None,
                  **kwargs):
        if currency is None:
            currency = self.get_currency()

        if price is None:
            price = Price(0, currency=currency)
        if chain:
            out = chain.execute(price=price, currency=currency, **kwargs)
            if out.has_key('price'):
                price = out['price']

        return price

    @link(namespace='product', name='list')
    def list_products(self, products, query=None, currency=None, index=None,
                      index_relation='product', **kwargs):
        if currency is None:
            currency = self.get_currency()
        
        if query is not None and index is not None:
            # See if we need to sort on price
            if ('sort', 'price') in query:
                pass
            elif ('sort', '-price') in query:
                pass
        return {
            'products': products
        }
