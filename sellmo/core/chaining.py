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
from inspect import isfunction

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
        captured = self.capture(**kwargs)
        if isinstance(captured, dict):
            kwargs.update(captured)
        elif isfunction(captured):
            func = captured
        
        out = func(module, self, **kwargs)
        return out
        
    def capture(self, **kwargs):
        out = dict()
        for func in reversed(self._capture_queue):
            response = func(**kwargs)
            if isinstance(response, dict):
                out.update(response)
                kwargs.update(response)
            elif response is False:
                break
            elif isfunction(response):
                return response
            elif not response is None:
                raise Exception("Func '%s' gave an unexpected response during capture fase." % func)
                    
        return out
        
    def execute(self, **kwargs):
        out = dict()
        for func in self._queue:
            response = func(**kwargs)
            if self.should_return(response):
                return response
            elif isinstance(response, dict):
                out.update(response)
                kwargs.update(response)
            elif response is False:
                break
            elif not response is None:
                raise Exception("Func '%s' gave an unexpected response during bubble fase." % func)
                
        return out
        
    @property
    def can_execute(self):
        return len(self._queue) > 0
    
    @property
    def can_capture(self):
        return len(self._capture_queue) > 0
        
    def should_return(self, response):
        return False
        
class ViewChain(Chain):
    
    def __init__(self, func, regex, **kwargs):
        super(ViewChain, self).__init__(func, **kwargs)
        self.regex = regex
        
    def handle(self, module, request, **kwargs):
        return super(ViewChain, self).handle(module=module, request=request, **kwargs)
    
    def capture(self, request, **kwargs):
        return super(ViewChain, self).capture(request=request, **kwargs)
        
    def execute(self, request, **kwargs):
        return super(ViewChain, self).execute(request=request, **kwargs)
    
    def should_return(self, response):
        return isinstance(response, HttpResponse)
        