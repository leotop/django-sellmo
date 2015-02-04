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

import sys
import logging


from django.apps import AppConfig
from django.conf import settings
from django.utils import six
from django.utils.importlib import import_module
from django.utils.module_loading import import_by_path, module_has_submodule

from sellmo import modules, params
from sellmo import celery, caching
from sellmo.core.loading import Loader
from sellmo.core.chaining import Chainer
from sellmo.signals.core import pre_init, post_init
from sellmo.api.configuration import define_setting


logger = logging.getLogger('sellmo')

class DummyLoader(object):
    
    calls = []
    
    def register(self, *args, **kwargs):
        self.calls.append((args, kwargs))


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
        
        # At this point Sellmo will begin to load
        pre_init.send(self)
        
        if celery.enabled:
            import sellmo.celery.integration
            sellmo.celery.integration.setup()
        
        if caching.enabled:
            import sellmo.caching.integration
            sellmo.caching.integration.setup()
        
        # At this point Django models can begin to load
        # by Sellmo's core modules.
        params.loader = Loader()
        
        # Also at this point, chains can be registered
        # by Sellmo's core modules.
        params.chainer = Chainer()
        
        # Load core modules
        for module in self.core_modules:
            import_by_path(module)
            
        # Remaining models will now be imported by Django
        # This does not happen in the desired order. Because
        # we want to enable a correct Django Template order, Sellmo
        # apps need to be configured in a reverse manner. As
        # we don't control the loading of models.py modules, we need
        # to adjust Sellmo's loading mechanism.
        params._loader = params.loader
        params.loader = DummyLoader()
        
    
    def ready(self):
        
        # Models have been imported (these are imported
        # reverse order, due to Django loading them. 
        # We correctly register these calls now.
        dummy = params.loader
        params.loader = params._loader
        del params._loader
        # Apply calls in reversed order
        for args in reversed(dummy.calls):
            params.loader.register(*args[0], **args[1])
        
        # Import .modules and .configure submodules for 
        # each Sellmo App
        imports = ['modules', 'configure']
        apps = list(six.itervalues(params.sellmo_apps))
        for module_name in imports:
            for app in reversed(apps):
                app.import_module(module_name)
                
        # At this point Sellmo's loading functionality
        # should no longer be used.
        loader = params.loader
        del params.loader
        
        # Delayed loading is now done. We can now call all
        # delayed functions in correct order.
        loader.load()
        
        # Initialize Sellmo modules now
        modules.init_modules()
        
        # Import extra modules for 
        # each Sellmo App. Like:
        # .views and .links.
        apps = list(six.itervalues(params.sellmo_apps))
        for module_name in params.extra_imports:
            for app in reversed(apps):
                app.import_module(module_name)
        
        # Everything has been imported and all chains 
        # should have been created and linked to by now.
        chainer = params.chainer
        del params.chainer
        
        # Hookup all chains
        chainer.hookup()
        
        # We are done
        post_init.send(self)