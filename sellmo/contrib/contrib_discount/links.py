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


from django.db.models import Q

from sellmo import modules
from sellmo.api.decorators import link
from sellmo.api.pricing import Price


namespace = modules.pricing.namespace


@link(namespace=modules.product.namespace, capture=True)
def list(request, discount_group=None, **kwargs):
    if discount_group is None:
        customer = modules.customer.get_customer(request=request)
        if customer and customer.is_authenticated():
            discount_group = customer.discount_group
    return {
        'discount_group' : discount_group,
    }
    

@link(namespace=modules.store.namespace)
def make_purchase(request, purchase, **kwargs):
    if modules.discount.user_discount_enabled:
        customer = modules.customer.get_customer(request=request)
        if customer and customer.is_authenticated():
            purchase.discount_group = customer.discount_group
            purchase.calculate(save=False)
    return {
        'purchase': purchase
    }


@link()
def get_price(price, product=None, discount_group=None, **kwargs):
    discounts = []
    if product:
        try:
            discount = modules.discount.Discount.objects.polymorphic()
            if modules.discount.user_discount_enabled:
                q = Q(groups=None)
                if discount_group:
                    q |= Q(groups=discount_group)
                discount = discount.filter(q)
            discount = discount.best_for_product(product)
            discounts.append(discount)
        except modules.discount.Discount.DoesNotExist:
            pass

    for discount in discounts:
        price = discount.apply(price)

    return {
        'price': price
    }
