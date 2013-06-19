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
from sellmo.core import chaining, loading
from sellmo.magic import singleton

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
    
    def __init__(self):
    
        # Init sellmo apps before initing modules allowing them to configure the class based modules
        apps = list(self._init_apps())
        
        # Init sellmo modules now to
        self._init_modules()
        
        self._load_apps(apps)
        self._link_apps(apps)
        self._link_apps(apps, '.links')
    
    def _init_apps(self):
        for app in settings.INSTALLED_APPS:
            mod = import_module(app)
            try:
                sellmo = import_module('%s.__sellmo__' % app)
            except Exception as exception:
                if module_has_submodule(mod, '__sellmo__'):
                    raise Exception(str(exception)), None, sys.exc_info()[2]
            else:
                sellmo.path = app
                yield sellmo
                
    def _init_modules(self):
        modules.init_pending_modules()
            
    def _load_apps(self, apps):
        loading.loader.load()
                        
    def _link_apps(self, apps, module='.views'):
        for app in apps:
            try:
                imported = import_module(module, app.path)
            except ImportError:
                continue
            else:
                kwargs = {
                    'namespace' : getattr(app, 'namespace', None),
                }
                for name in dir(imported):
                    attr = getattr(imported, name)
                    if hasattr(attr, '_im_linked'):
                        if not self._link(attr, **kwargs):
                            logger.warning("Could not link '%s.%s'"  % (attr.__module__, attr.__name__))
    
    def _link(self, link, namespace=None):
        if link._namespace:
            # override default namespace
            namespace = link._namespace
        
        if not namespace:
            raise Exception("Link '%s' does not define a namespace" % link)
        
        if not hasattr(modules, namespace):
            logger.warning("Module '%s' not found"  % namespace)
            return False
        
        module = getattr(modules, namespace)
        name = link._name
        
        if not hasattr(module, name) or not hasattr(getattr(module, name), '_chain'):
            logger.warning("Module '%s' has no chainable method '%s'"  % (namespace, link._name))
            return False
        
        chain = getattr(module, name)._chain
        chain.link(link)
        return True
        
