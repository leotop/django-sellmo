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

import magic
	
class MountPoint(magic.Singleton):
	
	def register(self, app):
		setattr(self, app.namespace, app)
		
	def unregister(self, app):
		setattr(self, app.namespace, None)
	
apps = MountPoint()

#

class _AppMeta(type):
	
	def __new__(meta, name, bases, dict):
		# create the app class
		cls = super(_AppMeta, meta).__new__(meta, name, bases, dict)
		
		# register the app at the mount point
		if cls.namespace:
			apps.register(cls)
		
		return cls

class App(object):
	
	__metaclass__ = _AppMeta
	enabled = True
	
	namespace = None
	prefix = None
	
	def __new__(cls, *args, **kwargs):
		if cls.enabled:
			app = object.__new__(cls)
			# Replace the class object with the actual app object
			apps.register(app)
			return app
		
		if cls.namespace:
			apps.unregister(cls)
			
		return None