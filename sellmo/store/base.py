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

from django.db.models import get_apps
from django.utils.importlib import import_module

#

import magic
from . import apps
from . import chaining

#

class Store(magic.Singleton):
	
	def __init__(self):
	
		# Mount external app representations
		mounted = list(self._mount_apps())
		
		# Core apps (order matters)
		self.product = apps.ProductApp()
		self.pricing = apps.PricingApp()
		self.store = apps.StoreApp()
		
		# 
		self.cart = apps.CartApp()
		self.customer = apps.CustomerApp()
		
		#
		self.checkout = apps.CheckoutApp()
		
		#
		self._link_apps(mounted)
		self._link_apps(mounted, '.gets', chaining.Chain)
	
	def _mount_apps(self):
		for app in get_apps():
			path = app.__name__
			assert path.endswith('.models'), """Invalid app module"""
			app_name = path[:-len('.models')]
			
			# Try to mount __sellmo__.py
			try:
				app = import_module('.__sellmo__', app_name)
				app.path = app_name
			except ImportError:
				continue
			
			yield app
						
	def _link_apps(self, apps, module='.views', chain_type=chaining.ViewChain):
		for app in apps:
			try:
				imported = import_module(module, app.path)
			except ImportError:
				continue
			else:
				for name in dir(imported):
					attr = getattr(imported, name)
					if hasattr(attr, '_im_linked'):
						self._link(attr, app.namespace, chain_type)
						
	
	def _link(self, link, namespace, chain_type):
		
		if link._namespace:
			# override default namespace
			namespace = link._namespace 
		
		assert hasattr(self, namespace), """Namespace '%s' not found"""  % namespace
		app = getattr(self, namespace)
		
		attr = '_%s_chain' % link._name
		if not hasattr(app, attr):
			setattr(app, attr, chain_type())
		
		links = getattr(app, attr)
		links.append(link)
		
		
	@property
	def apps(self):
		apps = [self.product, self.pricing, self.store]
		
		if self.cart:
			apps.append(self.cart)
			
		if self.checkout:
			apps.append(self.checkout)
			
		return apps
		
#
		
sellmo = Store()