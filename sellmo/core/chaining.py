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

from django.http import HttpResponse
from inspect import isfunction, isgeneratorfunction

#

class Chain(object):
    
    def __init__(self, func):
        self._queue = []
        self._capture_queue = []
        self._func = func
        
    def __nonzero__(self):
        return self.can_execute
    
    def link(self, func):
        if func._capture:
            self._capture_queue.append(func)
        else:
            self._queue.append(func)
            
    def handle(self, module, **kwargs):
        func = self._func
        
        # Capture
        out = self._loop(reversed(self._capture_queue), **kwargs)
        if not out[1] is None:
            if isfunction(out[1]):
                func = out[1]
            else:
                return out[1]
        
        kwargs = out[0]
        return func(module, self, **kwargs)
        
    def _loop(self, queue, **kwargs):
        for func in queue:
            # We allow for yieldable output
            if isgeneratorfunction(func):
                responses = list(func(**kwargs))
            else:
                responses = [func(**kwargs)]
            # Iterate through output
            for response in responses:
                if self.should_return(response):
                    # Return immediately
                    return (kwargs, response)
                elif isinstance(response, dict):
                    # Merge
                    kwargs.update(response)
                elif response is False:
                    # SKIP (1)
                    break
                elif response is None:
                    # Nothing to do, just keep on looping
                    continue
                else:
                    raise Exception("Func '%s' gave an unexpected response '%s'." % (func, response))
            else:
                # No break in inner loop, continue
                continue
            # SKIP (2)
            break
        return (kwargs, None)
    
    def execute(self, **kwargs):
        out = self._loop(self._queue, **kwargs)
        if not out[1] is None:
            return out[1]
        return out[0]
        
    @property
    def can_execute(self):
        return len(self._queue) > 0
    
    @property
    def can_capture(self):
        return len(self._capture_queue) > 0
        
    def should_return(self, response):
        return isfunction(response)
        
class ViewChain(Chain):
    
    def __init__(self, func, regex=None, **kwargs):
        super(ViewChain, self).__init__(func, **kwargs)
        self.regex = regex if not regex is None else []
        
    def handle(self, module, request, **kwargs):
        return super(ViewChain, self).handle(module=module, request=request, **kwargs)
    
    def capture(self, request, **kwargs):
        return super(ViewChain, self).capture(request=request, **kwargs)
        
    def execute(self, request, **kwargs):
        return super(ViewChain, self).execute(request=request, **kwargs)
    
    def should_return(self, response):
        return isinstance(response, HttpResponse) or super(ViewChain, self).should_return(response)
        