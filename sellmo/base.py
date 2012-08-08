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

class MountPoint(object):
	__metaclass__ = magic.SingletonMeta
	
apps = MountPoint()

#

class _AppMeta(magic.SingletonMeta):
	
	def __new__(meta, name, bases, dict):
		# create the app class
		cls = super(_AppMeta, meta).__new__(meta, name, bases, dict)
		
		# register the app type to the mount point
		if cls.enabled and cls.namespace:
			setattr(apps, cls.namespace, cls)
		
		return cls

class App(object):
	
	__metaclass__ = _AppMeta
	enabled = True
	
	namespace = None
	prefix = None
	
	def __new__(cls, *args, **kwargs):
		if cls.enabled:
			
			# Create the actual app
			app = object.__new__(cls)
			
			# Replace the class object with the actual app object
			setattr(apps, app.namespace, app)
			
			#
			return app
		else:
			# App is disabled, remove from mountpoint
			setattr(apps, cls.namespace, None)
			return None