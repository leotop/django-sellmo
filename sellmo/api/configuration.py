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


from django.conf import settings
from django.utils.module_loading import import_by_path


_prefix = 'SELLMO'

def _get_setting_key(key, prefix=None):
    if prefix:
        key = '{0}_{1}'.format(prefix, key)
    return key
    
def get_setting(key, prefix=_prefix, **kwargs):
    key = _get_setting_key(key, prefix)
    try:
        value = getattr(settings, key)
    except AttributeError:
        if 'default' in kwargs:
            value = kwargs['default']
        else:
            raise
    return value

def define_setting(key, required=True, transform=None, prefix=_prefix, 
                   **kwargs):
    return _LazySetting(
        _get_setting_key(key, prefix), required=required,
        transform=transform, **kwargs)
    
def define_import(key, required=True, prefix=_prefix, **kwargs):
    if 'transform' not in kwargs:
        transform = lambda path : import_by_path(path) if path else None
        kwargs['transform'] = transform
    return define_setting(
        key, required=required, **kwargs)
                   
class _LazySetting(object):
    
    def __init__(self, key, required=True, transform=None, **kwargs):
        self.key = key
        self.required = required
        self.transform = transform
        if 'default' in kwargs:
            self.default = kwargs['default']

    def _resolve(self):
        try:
            value = getattr(settings, self.key)
        except AttributeError:
            value = None
            if hasattr(self, 'default'):
                value = self.default
            elif self.required:
                raise
        
        if self.transform:
            value = self.transform(value)
        
        return value

    def __get__(self, obj, objtype):
        if not hasattr(self, '_value'):
            self._value = self._resolve()
        return self._value