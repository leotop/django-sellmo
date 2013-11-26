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

from django.core.cache import cache

#

from sellmo.core.chaining import link_func
from sellmo.signals.core import post_init
from sellmo.config import settings

#

def cached(cache, name, namespace=None, timeout=True):
	return cache(name, namespace, timeout)

class Cache(object):
	
	_im_linked = True
	_links = []
	
	#
	timeout = True
	prefix = settings.CACHING_PREFIX
	
	def __init__(self, name, namespace=None, timeout=True):
		post_init.connect(self._on_post_init)
		self._links = [
			link_func(self.capture, name=name, namespace=namespace, capture=True),
			link_func(self.finalize, name=name, namespace=namespace)
		]
		
		self.timeout = timeout
		
	def resolve_key(self, key):
		if self.prefix:
			return '_'.join([self.prefix, key])
		
	def set(self, key, value):
		key = self.resolve_key(key)
		args = [key, value]
		if self.timeout is not True:
			args += [self.timeout]
		cache.set(*args)
	
	def get(self, key, default=None):
		key = self.resolve_key(key)
		return cache.get(key, default)
		
	def delete(self, *keys):
		if len(keys) > 1:
			cache.delete_many([self.resolve_key(key) for key in keys])
		elif len(keys) == 1:
			cache.delete(self.resolve_key(keys[0]))
		
	def capture(self, *args, **kwargs):
		pass
		
	def finalize(self, *args, **kwargs):
		pass
		
	def hookup(self):
		pass
		
	def _on_post_init(self, sender, **kwargs):
		self.hookup()