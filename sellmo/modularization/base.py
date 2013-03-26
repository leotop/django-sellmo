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

from sellmo.magic import singleton, SingletonMeta

#

@singleton
class MountPoint(object):
	
	def __init__(self):
		self._pending = []
		self._modules = []
	
	def on_module_creation(self, module):
		if module.enabled:
			setattr(self, module.namespace, module)
			self._pending.append(module)
			self._modules.append(module)
			
	def on_module_init(self, module, instance):
		setattr(self, module.namespace, instance)
		
		# Remove class based module and add instance based module
		self._pending.remove(module)
		self._modules.remove(module)
		self._modules.append(instance)
			
	def init_pending_modules(self):
		while self._pending:
			module = self._pending[0]
			module()
			
	def __iter__(self):
		for module in self._modules:
			yield module
			
modules = MountPoint()

class _ModuleMeta(SingletonMeta):
	
	def __new__(meta, name, bases, dict):
		cls = super(_ModuleMeta, meta).__new__(meta, name, bases, dict)
		
		# Threat the actual 'Module' class not as a module
		if cls.__ignore__:
			cls.__ignore__ = False
			return cls
		
		# Validate the module
		if not cls.namespace:
			raise Exception("No namespace defined for module '%s'" % cls)
		
		# Signal mountpoint
		modules.on_module_creation(cls)
		
		return cls

class Module(object):
	
	__metaclass__ = _ModuleMeta
	__ignore__ = True
	
	enabled = True
	namespace = None
	prefix = None
	
	def __new__(cls, *args, **kwargs):
		module = None
		if cls.enabled:
			module = object.__new__(cls)
			
		modules.on_module_init(cls, module)
		return module