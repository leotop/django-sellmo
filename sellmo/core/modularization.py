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
import imp
import inspect

from sellmo.api.configuration import get_setting
from sellmo.signals.core import module_created, module_init
from django.core.exceptions import ImproperlyConfigured


try:
    _registry_module = get_setting('REGISTRY_MODULE', default='sellmo.registry')
except ImproperlyConfigured:
    _registry_module = 'sellmo.registry'


class MountPoint(object):

    def __init__(self):
        self._modules = {}
        self._create_registry(_registry_module, True)
        # Python module loading
        sys.meta_path.append(self)

    # Python module loading
    def find_module(self, fullname, path=None):
        if fullname.startswith(_registry_module):
            return self
        return None

    # Python module loading
    def load_module(self, fullname):
        if fullname in sys.modules:
            return sys.modules[fullname]
        raise ImportError()

    def _create_registry(self, fullname, package=False):
        module = sys.modules.setdefault(fullname, imp.new_module(fullname))
        module.__file__ = '<sellmo>'
        module.__loader__ = self
        if package:
            module.__path__ = []
            module.__package__ = fullname
        else:
            module.__package__ = fullname.rpartition('.')[0]
        return module

    def _on_module_class(self, module):
        self._modules[module.namespace] = module

        # Signal
        module_created.send(sender=self, module=module)

    def init_modules(self):
        for module in self._modules.values():
            # Make sure module hasn't been initialized already
            if not inspect.isclass(module):
                raise Exception(
                    "Module '{0}' has already been init.".format(module))
            
            # Initialize
            instance = module()

            # Override class based module with instance based module
            self._modules[module.namespace] = instance

            # Signal
            module_init.send(sender=self, module=instance)

    def __getattr__(self, name):
        if name in self._modules:
            return self._modules[name]
        raise AttributeError(name)

    def __iter__(self):
        for module in self._modules.itervalues():
            yield module


class _ModuleMeta(type):

    def __new__(cls, name, bases, attrs):
        out = super(_ModuleMeta, cls).__new__(cls, name, bases, attrs)

        # __new__ will also be called for the Module class. Do not proceed
        # with any further initialization. Ignore it..
        if out.__ignore__:
            out.__ignore__ = False
            return out

        # See if this module is enabled. If not, no further initialization
        # is needed.
        if not out.enabled:
            return out

        # Validate the module
        if not out.namespace:
            raise Exception(
                "No namespace defined for module '{0}'".format(out))

        # Create the registry (python)module for this module
        out._registry = modules._create_registry(
            '{0}.{1}'.format(_registry_module, out.namespace))
        setattr(sys.modules[_registry_module], out.namespace, out._registry)

        # Register attributes
        for name, value in attrs.iteritems():
            setattr(out, name, value)

        modules._on_module_class(out)
        return out
        
    def can_register_type(cls, value):
        allowed = ['sellmo', cls.namespace]
        if value.__module__ and not value.__module__.startswith(_registry_module):
            root = value.__module__.split('.')[0]
            if root not in allowed:
                return False
        return True
    
    def __setattr__(cls, name, value):
        super(_ModuleMeta, cls).__setattr__(name, value)
        if not name.startswith('_'):
            if isinstance(value, type):
                if cls.can_register_type(value):
                    value.__module__ = cls._registry.__name__
                else:
                    raise Exception("Cannot register {0} in module {1}".format(value, cls))
            setattr(cls._registry, name, value)


class Module(object):

    __metaclass__ = _ModuleMeta
    # __new__ will also be called for the Module class. We need a flag
    # to ignore it.
    __ignore__ = True

    enabled = True
    namespace = None


modules = MountPoint()
