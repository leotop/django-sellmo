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

from django.conf import settings
from django.utils.importlib import import_module
from django.utils.module_loading import module_has_submodule

#

from sellmo import modules
from sellmo.core import chaining
from sellmo.magic import singleton

#

import sys, logging
from collections import deque
from copy import copy

#

logger = logging.getLogger('sellmo')

# 

class NotLinkedException(Exception):
	pass

@singleton
class Sellmo(object):
	
	def __init__(self):
	
		# Init sellmo apps before initing modules allowing them to configure the class based modules
		apps = list(self._init_apps())
		
		# Init sellmo modules now to
		self._init_modules()
		
		self._load_apps(apps)
		self._link_apps(apps)
		self._link_apps(apps, '.gets')
	
	def _init_apps(self):
	
		for app in settings.INSTALLED_APPS:
			mod = import_module(app)
			try:
				sellmo = import_module('%s.__sellmo__' % app)
			except Exception as exception:
				if module_has_submodule(mod, '__sellmo__'):
					raise Exception(str(exception)), None, sys.exc_info()[2]
			else:
				sellmo.path = app
				yield sellmo
				
	def _init_modules(self):
		modules.init_pending_modules()
		for module in modules:
			for name in dir(module):
				attr = getattr(module, name)
				if hasattr(attr, '_im_chainable'):
					self._init_chain(module, attr)
				
	def _init_chain(self, module, func):
		name = '_%s_chain' % func._name
		if hasattr(module, name):
			raise Exception()
			
		chain = chaining.Chain
		if getattr(func, '_im_view', False):
			chain = chaining.ViewChain
		chain = chain()
		setattr(module, name, chain)		
			
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
						
	def _link_apps(self, apps, module='.views'):
		for app in apps:
			try:
				imported = import_module(module, app.path)
			except ImportError:
				continue
			else:
				kwargs = {
					'namespace' : getattr(app, 'namespace', None),
				}
				for name in dir(imported):
					attr = getattr(imported, name)
					if hasattr(attr, '_im_linked'):
						if not self._link(attr, **kwargs):
							logger.warning("Could not link '%s.%s'"  % (attr.__module__, attr.__name__))
	
	def _link(self, link, namespace=None):
		if link._namespace:
			# override default namespace
			namespace = link._namespace
		
		if not namespace:
			raise Exception("Link '%s' does not define a namespace" % link)
		
		if not hasattr(modules, namespace):
			logger.warning("Module '%s' not found"  % namespace)
			return False
		
		module = getattr(modules, namespace)
		name = '_%s_chain' % link._name	
		
		if not hasattr(module, name):
			logger.warning("Module '%s' has no chainable method '%s'"  % (namespace, link._name))
			return False
		
		links = getattr(module, name)
		links.append(link)
		return True
		
