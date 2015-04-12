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

from sellmo import modules, Module
from sellmo.api.decorators import chainable
from sellmo.api.configuration import define_setting
from sellmo.contrib.pricing.models import (QtyPriceBase,
                                                   QtyPrice,
                                                   QtyPriceRatio,
                                                   ProductQtyPrice)
from sellmo.core.query import PKIterator

from django.db import transaction
from django.db.models.query import QuerySet
from django.utils import timezone


logger = logging.getLogger('sellmo')


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


class PriceIndexingModule(Module):
    namespace = 'price_indexing'

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
                'kwargs': {},
            }

    def _write_updates(self, handle, updates):
        handle.updates = updates
        handle.save()

    def _merge_kwarg(self, index, key, existing, new):
        merged = list(existing)
        merged.extend([value for value in new if value not in existing])
        return merged
        
    def _convert_kwarg(self, index, key, value):
        if index.kwargs[key].get('model', None) is not None:
            if isinstance(value, QuerySet):
                return list(value.values_list('pk', flat=True))
            else:
                return [obj.pk for obj in value]
        else:
            return list(value)

    @chainable()
    def queue_update(self, chain, identifier, **kwargs):
        index = modules.pricing.get_index(identifier)
        with transaction.atomic():
            handle = self._get_handle(index)
            updates = self._read_updates(handle)

            # Merge kwargs
            existing = dict(updates['kwargs'])
            for key, value in kwargs.iteritems():
                if not value:
                    # Skip empty lists (or querysets)
                    continue
                
                value = self._convert_kwarg(index, key, value)
                if key in existing:
                    value = self._merge_kwarg(key, index, existing[key], value)
                existing[key] = value
            
            updates['kwargs'] = existing
            self._write_updates(handle, updates)
            
    @chainable()
    def handle_updates(self, chain, **kwargs):
        for identifier, index in modules.pricing.indexes.iteritems():
            self._handle_updates(identifier, index)
            
    def _handle_updates(self, identifier, index):
        with transaction.atomic():
            handle = self._get_handle(identifier)
            if handle.updates is None:
                # Nothing to update
                return
            # Read and clear updates
            updates = self._read_updates(handle)
            self._write_updates(handle, None)
        
        logger.info("Index '{0}' is updating.".format(identifier))
        
        # Resolve actual kwargs
        kwargs = {}
        for key, value in updates['kwargs'].iteritems():
            if index.kwargs[key].get('model', None) is not None:
                model = index.kwargs[key]['model']
                kwargs[key] = PKIterator(model, value)
            else:
                kwargs[key] = value
        
        combinations = modules.pricing.update_index(
            identifier=identifier,
            delay=True,
            **kwargs
        )
        
        logger.info("Updating {1} indexes for index '{0}'"
                    .format(identifier, len(combinations)))
    
        with transaction.atomic():
            for combination in combinations:
                price = modules.pricing.get_price(**combination)
                signature = ", ".join(str(value) for value in 
                                      combination.values())
                
                if index.index(price, **combination):
                    logger.info("Index {1}={2} created for index '{0}'"
                        .format(identifier, signature, price.amount))
                else:
                    logger.info("Index {1}={2} omitted for index '{0}'"
                        .format(identifier, signature, price.amount))
            
            handle = self._get_handle(identifier)
            handle.updated = timezone.now()
            handle.save()
        
        logger.info("Index '{0}' updated.".format(index))
        


