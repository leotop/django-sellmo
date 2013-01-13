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

def load(action=None, after=None):
	def decorator(func):
		if not hasattr(func, '_im_loadable'):
			func._actions = []
			func._delays = []
		
		if action:
			func._actions.append(action)
			
		if after:
			func._delays.append(after)
			
		func._im_loadable = True
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
	
def view(regex=None, name=None, namespace=None):
	
	def decorator(func):
	
		def view(self, request, **kwargs):
			chain = getattr(self, '_%s_chain' % func.func_name, None)
			if chain:
				# Capture
				captured = chain.capture(request, **kwargs)
				kwargs.update(captured)
			
			response = func(self, chain, request, **kwargs)
			return response
		
		view._im_chainable = True
		view._im_view = True
		view._regex = regex
		view._name = name if name else func.func_name
		view._namespace = namespace
		
		return view
		
	return decorator
	
def chainable(name=None, namespace=None):
	
	def decorator(func):
		
		def chainable(self, **kwargs):
			chain = getattr(self, '_%s_chain' % func.func_name, None)
			if chain:
				# Capture
				captured = chain.capture(**kwargs)
				kwargs.update(captured)
			
			result = func(self, chain, **kwargs)
			return result
			
		chainable._im_chainable = True
		chainable._im_get = True
		chainable._name = name if name else func.func_name
		chainable._namespace = namespace
		
		return chainable
		
	return decorator