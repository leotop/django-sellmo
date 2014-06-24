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
from sellmo.core.local import get_context
from sellmo.api.decorators import link
from sellmo.api.pricing import Price


namespace = modules.pricing.namespace


@link()
def retrieve(stampable, prop, price=None, **kwargs):
    field = '{0}_tax_tax'.format(prop)
    tax_id = getattr(stampable, '{0}_id'.format(field), None)
    if tax_id is not None:
        context = get_context()
        taxes = context.get('taxes', {})
        if not tax_id in taxes:
            # Query now
            taxes[tax_id] = getattr(stampable, field)
            context['taxes'] = taxes
        price.context['tax'] = taxes[tax_id]
    return {
        'price': price
    }


@link()
def stamp(stampable, prop, price, **kwargs):
    if 'tax' in price.context:
        field = '{0}_tax_tax'.format(prop)
        setattr(stampable, field, price.context['tax'])


@link()
def get_price(price, product=None, shipping_method=None, payment_method=None, 
              **kwargs):
    tax = None
    if product:
        try:
            tax = modules.tax.Tax.objects.polymorphic() \
                         .get_best_for_product(product)
        except modules.tax.Tax.DoesNotExist:
            tax = None
    elif shipping_method or payment_method:
        settings = modules.settings.get_settings()
        if shipping_method and settings.shipping_costs_tax:
            tax = settings.shipping_costs_tax.downcast()
        elif shipping_method and settings.payment_costs_tax:
            tax = settings.payment_costs_tax.downcast()

    if tax:
        price = tax.apply(price)

    return {
        'price': price
    }
