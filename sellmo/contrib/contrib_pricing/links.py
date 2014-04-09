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


from django.http import HttpResponse

from sellmo import modules
from sellmo.config import settings
from sellmo.api.decorators import link
from sellmo.core.params import params
from sellmo.api.pricing import Price
from sellmo.contrib.contrib_pricing import tasks


namespace = modules.pricing.namespace


@link()
def get_price(price, product=None, currency=None, qty=1, **kwargs):
    if product and not price:
        try:
            qty_price = modules.qty_pricing.ProductQtyPrice.objects.filter(
                product=product).for_qty(qty)
        except modules.qty_pricing.ProductQtyPrice.DoesNotExist:
            pass
        else:
            price = qty_price.apply(price)
        return {
            'price': price
        }

if settings.CELERY_ENABLED and not getattr(params, 'worker_mode', False):
    @link(capture=True)
    def update_index(index, invalidations, **kwargs):
        yield override_update_index


def override_update_index(module, chain, index, invalidations, **kwargs):
    tasks.queue_update.apply_async((index, invalidations), kwargs)
