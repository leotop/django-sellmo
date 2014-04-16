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
    
def get_setting(key, default=None, prefix=_prefix):
    return getattr(settings, _get_setting_key(key, prefix), default)

def setting(key, default=None, required=True, transform=None, prefix=_prefix):
    return LazySetting(
        key, default=default, required=required, transform=transform)
    

def class_setting(key, default=None, required=True, prefix=_prefix):
    return LazySetting(
        key, default=default, required=required,
        transform = lambda path : import_by_path(path))
        

class LazySetting(object):

    _is_resolved = False
    _value = None

    def __init__(self, key, default=None, required=True, transform=None,
                 prefix=_prefix):
        self.key = _get_setting_key(key, prefix)
        self.default = default
        self.required = required
        self.transform = transform

    def _resolve(self):
        value = self.default
        try:
            value = getattr(settings, self.key)
        except AttributeError:
            if self.default is None and self.required:
                raise

        if self.transform and value is not None:
            value = self.transform(value)

        self._value = value
        self._is_resolved = True

    def __get__(self, obj, objtype):
        if not self._is_resolved:
            self._resolve()
        return self._value