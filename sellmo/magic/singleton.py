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


# Dummy method, assigned the 2nd time an instance is made.
def __init__(self, *args, **kwargs):
    pass


# Descriptor for __new__ method
class SingletonAccess(object):

    def __init__(self, cls, new):
        self._cls = cls
        self._new = new
        self._instance = None

    def __get__(self, obj, objtype):
        if objtype == self._cls:
            return self._get_instance
        else:
            return self._new

    def __set__(self, obj, val):
        raise Exception()

    def _get_instance(self, cls, *args, **kwargs):
        if not self._instance:
            # Create first and only instance by calling original __new__
            self._instance = self._new(cls, *args, **kwargs)
        return self._instance

# Descriptor for ___init__ method


class OneTimeInitAccess(object):

    def __init__(self, cls, init):
        self._cls = cls
        self._init = init
        self._omit = False

    def __get__(self, obj, objtype):
        init = self._init
        if objtype == self._cls:
            if self._omit:
                init = __init__
            self._omit = True
        return init.__get__(obj, objtype)

    def __set__(self, obj, val):
        raise Exception()

# Usage option 1: __metaclass__ assignment


class SingletonMeta(type):

    def __new__(cls, name, bases, dict):
        out = super(SingletonMeta, cls).__new__(cls, name, bases, dict)
        out.__new__ = SingletonAccess(out, out.__new__)
        out.__init__ = OneTimeInitAccess(out, out.__init__)
        return out

# Usage option 2: decorator usage


def singleton(cls):
    cls.__new__ = SingletonAccess(cls, cls.__new__)
    cls.__init__ = OneTimeInitAccess(cls, cls.__init__)
    return cls
