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


from django.db import models
from django.db.models.query import QuerySet

import sellmo
from sellmo import modules
from sellmo.api.decorators import view, chainable
from sellmo.api.store.models import Purchase


class StoreModule(sellmo.Module):

    namespace = 'store'
    Purchase = Purchase

    @chainable()
    def merge_purchase(self, chain, purchase, existing_purchases,
                       result=None, **kwargs):

        for existing in existing_purchases:
            if not existing.pk:
                raise Exception("Can only merge persistent existing purchases")

        purchase = purchase.downcast()
        manager = purchase.__class__.objects

        # Ensure existing_purchases is a queryset of the given purchase's
        # queryset type
        existing_purchases = manager.filter(
            pk__in=[existing.pk for existing in existing_purchases])

        # Find an existing purchase
        try:
            result = existing_purchases.mergeable_with(purchase)
        except self.Purchase.DoesNotExist:
            return None

        # Merge this existing purchase with the new purchase
        result.merge_with(purchase)

        # Remake the purchase
        self.make_purchase(purchase=result)

        if chain:
            out = chain.execute(
                purchase=purchase, existing_purchases=existing_purchases, 
                result=result, **kwargs)
            result = out.get('result', result)

        return result

    @chainable()
    def make_purchase(self, chain, product=None, qty=None, purchase=None,
                      **kwargs):

        if purchase is None:
            purchase = self.Purchase()

        if not product is None:
            purchase.product = product
            purchase.description = unicode(product)

        if not qty is None:
            purchase.qty = qty

        purchase.calculate(save=False)

        if chain:
            out = chain.execute(
                product=purchase.product, qty=purchase.qty, 
                purchase=purchase, **kwargs)
            purchase = out.get('purchase', purchase)

        return purchase
