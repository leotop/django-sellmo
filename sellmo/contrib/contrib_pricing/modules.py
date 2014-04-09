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
from datetime import datetime

from sellmo import modules, Module
from sellmo.api.decorators import chainable
from sellmo.contrib.contrib_pricing.models import (QtyPriceBase,
                                                   QtyPrice,
                                                   QtyPriceRatio,
                                                   ProductQtyPrice,
                                                   PriceIndexHandle)

from django.db import transaction
from django.db.models.query import QuerySet


logger = logging.getLogger('sellmo')


class QtyPricingModule(Module):
    namespace = 'qty_pricing'

    QtyPriceBase = QtyPriceBase
    QtyPrice = QtyPrice
    QtyPriceRatio = QtyPriceRatio
    ProductQtyPrice = ProductQtyPrice

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


class PriceIndexingModule(Module):
    namespace = 'price_indexing'

    PriceIndexHandle = PriceIndexHandle

    def _get_handle(self, index):
        if self.PriceIndexHandle.objects.filter(index=index).count() == 0:
            self.PriceIndexHandle.objects.create(index=index)
        return self.PriceIndexHandle.objects.select_for_update() \
                                            .get(index=index)

    def _read_updates(self, handle):
        if handle.updates:
            return handle.updates
        else:
            return {
                'invalidations': modules.pricing.get_index(handle.index) \
                                                .model.objects.none(),
                'kwargs': {},
            }

    def _write_updates(self, handle, updates):
        handle.updates = updates
        handle.save()

    def _merge_kwarg(self, key, existing, new):
        if isinstance(existing, QuerySet) and isinstance(new, QuerySet):
            # Make sure we are dealing with the same model
            if existing.model != new.model:
                raise Exception(
                    "Cannot merge query sets '{0}'."
                    .format(key))
            merged = [pk for pk in existing.values_list('pk', flat=True)]
            merged.extend(
                [pk for pk in new.values_list('pk', flat=True)
                 if pk not in merged])
            merged = existing.model.objects.filter(pk__in=merged)
        else:
            merged = list(existing)
            merged.extend([value for value in new if value not in existing])
        return merged

    @chainable()
    def queue_update(self, chain, index, invalidations, **kwargs):
        with transaction.atomic():
            handle = self._get_handle(index)
            updates = self._read_updates(handle)

            # Merge invalidations
            existing = updates['invalidations']
            merged = [pk for pk in existing.values_list('pk', flat=True)]
            merged.extend(
                [pk for pk in invalidations.values_list('pk', flat=True)
                 if pk not in merged])
            updates['invalidations'] = modules.pricing.get_index(
                index).model.objects.filter(pk__in=merged)

            # merge kwargs
            merged = dict(updates['kwargs'])
            for key, value in kwargs.iteritems():
                if not value:
                    # Skip empty lists (or querysets)
                    continue
                if key not in merged:
                    merged[key] = value
                else:
                    merged[key] = self._merge_kwarg(key, merged[key], value)
            updates['kwargs'] = merged
            self._write_updates(handle, updates)

    @chainable()
    def handle_updates(self, chain, **kwargs):
        for identifier, index in modules.pricing.indexes.iteritems():
            with transaction.atomic():
                handle = self._get_handle(identifier)
                if handle.updates is None:
                    continue
                updates = self._read_updates(handle)
                self._write_updates(handle, None)

            logger.info("Index '{0}' is updating.".format(identifier))

            # Requery kwargs (query could have become invalid)
            for key, value in updates['kwargs'].iteritems():
                if index.kwargs[key].get('model', None) is not None:
                    model = index.kwargs[key]['model']
                    updates['kwargs'][key] = model.objects.filter(
                        pk__in=value.values_list('pk', flat=True))

            # Requery invalidations
            invalidations = updates['invalidations']
            updates['invalidations'] = invalidations.model.objects.filter(
                pk__in=invalidations.values_list('pk', flat=True))

            invalidations, combinations = modules.pricing.update_index(
                index=identifier,
                invalidations=updates['invalidations'],
                delay=True,
                **updates['kwargs']
            )

            with transaction.atomic():
                logger.info("Invalidating {1} indexes for index '{0}'".format(
                    identifier, invalidations.count()))
                invalidations.invalidate()

                logger.info(
                    "Creating {1} indexes for index '{0}'"
                    .format(identifier, len(combinations)))
                for combination in combinations:
                    price = modules.pricing.get_price(**combination)
                    signature = ", ".join(str(value)
                                          for value in combination.values())
                    if index.index(price, **combination):
                        logger.info(
                        "Index {1}={2} created for index '{0}'"
                        .format(identifier, signature, price.amount))
                    else:
                        logger.info(
                            "Index {1}={2} omitted for index '{0}'"
                            .format(identifier, signature, price.amount))

            with transaction.atomic():
                handle = self._get_handle(identifier)
                handle.updated = datetime.now()
                handle.save()

            logger.info("Index '{0}' updated.".format(index))
