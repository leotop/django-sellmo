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
from sellmo.api.decorators import chainable
from sellmo.api.configuration import define_setting
from sellmo.contrib.pricing.models import (QtyPriceBase,
                                                   QtyPrice,
                                                   QtyPriceRatio,
                                                   ProductQtyPrice)


class QtyPricingModule(Module):
    namespace = 'qty_pricing'

    QtyPriceBase = QtyPriceBase
    QtyPrice = QtyPrice
    QtyPriceRatio = QtyPriceRatio
    ProductQtyPrice = ProductQtyPrice
    
    indexable_qtys = define_setting(
        'INDEXABLE_QTYS',
        default=[1])
    
    @chainable()
    def get_tiers(self, chain, product, tiers=None, **kwargs):
        if not tiers:
            tiers = product.qty_prices.all()
        if chain:
            out = chain.execute(product=product, tiers=tiers, **kwargs)
            tiers = out.get('tiers', tiers)
        return tiers

    @chainable()
    def get_tier(self, chain, product, qty, tier=None, **kwargs):
        if not tier:
            try:
                tier = product.qty_prices.for_qty(qty)
            except self.ProductQtyPrice.DoesNotExist:
                pass
        if chain:
            out = chain.execute(product=product, qty=qty, tier=tier, **kwargs)
            tier = out.get('tier', tier)
        return tier
