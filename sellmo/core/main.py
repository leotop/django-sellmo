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
from collections import deque
from copy import copy

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
        
        # Init sellmo apps before initing modules allowing them to configure the class based modules
        apps = list(self._init_apps())
        
        # 
        self._init_modules()
        self._link_modules()
        
        #
        self._load_apps(apps)
        for link in self.links:
            self._link_apps(apps, link)
            
        post_init.send(self)
    
    def _init_apps(self):
        for app in settings.INSTALLED_APPS:
            sellmo_module = self._load_app_module(app, '__sellmo__')
            if sellmo_module:
                sellmo_module.path = app
                yield sellmo_module
                
    def _link_apps(self, apps, module_name):
        for app in apps:
            app_module = self._load_app_module(app.path, module_name)
            if app_module:
                kwargs = {
                    'namespace' : getattr(app, 'namespace', None),
                }
                for name in dir(app_module):
                    attr = getattr(app_module, name)
                    if hasattr(attr, '_im_linked'):
                        self._handle_linked_attr(attr, **kwargs)
                
                        
    def _load_app_module(self, app, module_name):
        app_module = import_module(app)
        try:
            module = import_module('{0}.{1}'.format(app, module_name))
        except Exception as exception:
            if module_has_submodule(app_module, module_name):
                raise Exception(str(exception)), None, sys.exc_info()[2]
        else:
            return module
                
    def _init_modules(self):
        modules.init_pending_modules()
            
    def _load_apps(self, apps):
        loading.loader.load()
                        
    def _link_modules(self):
        for module in modules:
            for name in dir(module):
                attr = getattr(module, name)
                if hasattr(attr, '_im_linked'):
                    self._handle_linked_attr(attr)
    
    def _handle_linked_attr(self, attr, **kwargs):
        links = getattr(attr, '_links', [attr])
        for link in links:
            if not self._link(link, **kwargs):
                logger.warning("Could not link '{0}.{1}'".format(link.__module__, link.__name__))
    
    def _link(self, link, namespace=None):
        if link._namespace:
            # override default namespace
            namespace = link._namespace
        
        if not namespace:
            logger.warning("Link '{0}.{1}' has no target namespace.".format(link.__module__, link.__name__))
            return False
        
        if not hasattr(modules, namespace):
            logger.warning("Module '{0}' not found".format(namespace))
            return False
        
        module = getattr(modules, namespace)
        name = link._name
        
        if not hasattr(module, name) or not hasattr(getattr(module, name), '_chain'):
            logger.warning("Module '{0}' has no chainable method '{1}'".format(namespace, link._name))
            return False
        
        chain = getattr(module, name)._chain
        chain.link(link)
        return True
        
