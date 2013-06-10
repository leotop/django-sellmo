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

from sellmo.core.loading import loader
from sellmo.core.chaining import Chain, ViewChain

def load(action=None, after=None, before=None):
    def decorator(func):
        loader.register(func, action=action, after=after, before=before)
        return func
    
    return decorator
    
def link(name=None, namespace=None, capture=False):
    def decorator(func):
        func._name = name if name else func.func_name
        func._namespace = namespace
        func._capture = capture
        func._im_linked = True
        return func
    
    return decorator
    
def view(regex=None):
    def decorator(func):
        chain = ViewChain(func, regex=regex)
        def wrapper(self, request, **kwargs):
            return chain.handle(module=self, request=request, **kwargs)
        wrapper._chain = chain
        return wrapper
    return decorator
    
def chainable():
    def decorator(func):
        chain = Chain(func)
        def wrapper(self, **kwargs):
            return chain.handle(module=self, **kwargs)
        wrapper._chain = chain
        return wrapper
    return decorator