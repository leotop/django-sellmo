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

import logging

#

from sellmo import modules, Module
from sellmo.api.decorators import chainable
from sellmo.contrib.contrib_pricing.models import QtyPriceBase, QtyPrice, QtyPriceRatio, ProductQtyPrice, PriceIndexHandle

#

from django.db import transaction
from django.db.models.query import QuerySet

#

logger = logging.getLogger('sellmo')

#

class QtyPricingModule(Module):
    namespace = 'qty_pricing'
    
    QtyPriceBase = QtyPriceBase
    QtyPrice = QtyPrice
    QtyPriceRatio = QtyPriceRatio
    ProductQtyPrice = ProductQtyPrice
    
    @chainable()
    def get_qty_tiers(self, chain, product, tiers=None, **kwargs):
        if not tiers:
            q = product.qty_prices.all()
            if q:
                tiers =  q
        if chain:
            out = chain.execute(product=product, tiers=tiers, **kwargs)
            if out.has_key('tiers'):
                tiers = out['tiers']
        return tiers
        
class PriceIndexingModule(Module):
    namespace = 'price_indexing'
    
    PriceIndexHandle = PriceIndexHandle
    
    def _get_handle(self, index):
        if self.PriceIndexHandle.objects.filter(index=index).count() == 0:
            self.PriceIndexHandle.objects.create(index=index)
        return self.PriceIndexHandle.objects.select_for_update().get(index=index)
        
    def _read_updates(self, handle):
        if handle.updates:
            return handle.updates
        else:
            return {
                'invalidations' : modules.pricing.get_index(handle.index).model.objects.none(),
                'kwargs' : {},
            }
            
    def _write_updates(self, handle, updates):
        handle.updates = updates
        handle.save()
        
    def _ensure_query_set(self, values):
        if not isinstance(values, QuerySet):
            return values[0].__class__.objects.filter(pk__in=[value.pk for value in values])
        return values
        
    def _merge_kwarg(self, key, existing, new):
        if isinstance(existing, QuerySet) or isinstance(new, QuerySet):
            existing = self._ensure_query_set(existing)
            new = self._ensure_query_set(new)
            # Make sure we are dealing with the same model
            if existing.model != new.model:
                raise Exception("Cannot merge kwarg '{0}'.".format(key))
            merged = [pk for pk in existing.values_list('pk', flat=True)]
            merged.extend([pk for pk in new.values_list('pk', flat=True) if pk not in merged])
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
            merged.extend([pk for pk in invalidations.values_list('pk', flat=True) if pk not in merged])
            updates['invalidations'] = modules.pricing.get_index(index).model.objects.filter(pk__in=merged)
            
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
        for index in modules.pricing.indexes.keys():
            with transaction.atomic():
                handle = self._get_handle(index)
                if handle.updates is None:
                    continue
                updates = self._read_updates(handle)
                self._write_updates(handle, None)
            
            modules.pricing.update_index(index=index, invalidations=updates['invalidations'], **updates['kwargs'])
    