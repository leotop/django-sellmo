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

from collections import deque
from copy import copy

#

class Store(object):
	
	__metaclass__ = magic.SingletonMeta
	
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
		self._load_apps(mounted)
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
			
	def _load_apps(self, apps):
		loadables = deque()
		for app in apps:
			for name in dir(app):
				attr = getattr(app, name)
				if hasattr(attr, '_im_loadable'):
					loadables.append(attr)
			
		
		# note: loadabels is already partially sorted due to the app order
		# 		make sure to keep this order
		
		actions = {}
		delays = {}
		
		executions = deque()
		delayed = deque()
		
		# Seperate non delayed loadables from delayed loadables
		while loadables:
			loadable = loadables.popleft()
			
			# Map actions to this loadable
			for action in loadable._actions:
				if not actions.has_key(action):
					actions[action] = []
				
				actions[action].append(loadable)
				
			# Map delays to this loadable
			for delay in loadable._delays:
				if not delays.has_key(delay):
					delays[delay] = []
				
				delays[delay].append(loadable)
			
			if not loadable._delays:
				# loadable has no delays, append to execution queue
				executions.append(loadable)
			else:
				delayed.append(loadable)
			
			
		# Seperate unnecessarily delayed loadables from valid delayed loadables
		loadables = delayed
		delayed = deque()
		while loadables:
			loadable = loadables.popleft()
			for delay in loadable._delays:
				if actions.has_key(delay):
					delayed.append(loadable)
					break
			else:
				executions.append(loadable)
			
		# Begin execution
		while executions:
			execution = executions.popleft()
			
			# Execute
			execution()
			
			# Remove from actions
			for action in execution._actions:
				actions[action].remove(execution)
				if not actions[action]:
					del actions[action]
					
			# Find loadables for (re)evaluation
			evaluations = deque()
			for action in execution._actions:
				if delays.has_key(action):
					for loadable in delays[action]:
						if loadable in delayed and not loadable in evaluations:
							evaluations.append(loadable)
						
			# (Re-)evaluate loadables
			while evaluations:
				loadable = evaluations.popleft()				
				for delay in loadable._delays:
					if actions.has_key(delay):
						# Still another delay
						break
				else:
					# No more valid delays
					delayed.remove(loadable)
					executions.append(loadable)
		
		# Verify for remaining delays
		if delayed:
			raise Exception("""Failed to load""")
						
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