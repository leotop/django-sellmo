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

from django.db.models.loading import get_apps
from django.conf import settings
from django.utils.importlib import import_module
from django.utils.module_loading import module_has_submodule

#

from sellmo import modules
from sellmo.magic import singleton
from sellmo.core import chaining, loading
from sellmo.signals.core import pre_init, post_init

#

import sys, logging

#

logger = logging.getLogger('sellmo')

# 

class NotLinkedException(Exception):
    pass

@singleton
class Sellmo(object):
    
    links = ['views', 'links']
    
    def __init__(self):
    
        pre_init.send(self)
        logger.info("Sellmo initializing...")
        
        # 1. First init & collect each django app which defines a __sellmo__ python module.
        apps = list(self._init_apps())
        
        # 2. Find additional modules in each app
        self._load_apps(apps, 'modules')
        
        # 3. Allow every app to configure modules
        self._load_apps(apps, 'configure')
        
        # 4. Begin the loading process as declared in all of the sellmo apps.
        loading.loader.load()
        
        # 5. Make sure every sellmo module registered to the mountpoint is instanciated.
        modules.init_modules()
        
        # 6. Load link modules
        for module_name in self.links:
            self._load_apps(apps, module_name)
        
        # 7. Hookup links
        chaining.chainer.hookup()
    
        logger.info("Sellmo initialized")
        post_init.send(self)
        
    
    def _init_apps(self):
        
        # We need to make sure every app's models in INSTALLED_APPS is loaded.
        get_apps()
        
        # 
        for app in settings.INSTALLED_APPS:
            sellmo_module = self._load_app_module(app, '__sellmo__')
            if sellmo_module:
                sellmo_module.path = app
                yield sellmo_module
                
    def _load_apps(self, apps, module_name):
        for app in apps:
            self._load_app_module(app.path, module_name)
                      
    def _load_app_module(self, app, module_name):
        app_module = import_module(app)
        try:
            module = import_module('{0}.{1}'.format(app, module_name))
        except Exception as exception:
            if module_has_submodule(app_module, module_name):
                raise Exception(str(exception)), None, sys.exc_info()[2]
        else:
            return module
