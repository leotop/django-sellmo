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


from django.apps import AppConfig
from django.utils.module_loading import import_by_path

from sellmo import celery, caching
from sellmo.core.main import Sellmo
from sellmo.api.configuration import define_setting


class DefaultConfig(AppConfig):
    name = 'sellmo'
    core_modules  = define_setting(
        'SELLMO_CORE_MODULES',
        default=[
            'sellmo.core.modules.pricing.PricingModule',
            'sellmo.core.modules.product.ProductModule',
            'sellmo.core.modules.store.StoreModule',
            'sellmo.core.modules.cart.CartModule',
            'sellmo.core.modules.checkout.CheckoutModule',
            'sellmo.core.modules.customer.CustomerModule',
        ]
    )
    
    def __init__(self, *args, **kwargs):
        super(DefaultConfig, self).__init__(*args, **kwargs)
        
        # Load core modules
        for module in self.core_modules:
            import_by_path(module)
            
        if celery.enabled:
            import sellmo.celery.integration
            sellmo.celery.integration.setup()
        
        if caching.enabled:
            import sellmo.caching.integration
            sellmo.caching.integration.setup()
    
    def ready(self):
        sellmo = Sellmo()