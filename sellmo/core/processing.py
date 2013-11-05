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

#

from collections import deque

#

class ProcessError(Exception):
	pass

class Process(object):
	
	def __init__(self):
		self._current_step = None
		
	def step_to(self, key):
		"""
		Tries to move one forward from the first step, untill the given step is matched.
		All intermediate steps need to be completed succesfully.
		"""
		step = self.get_first_step()
		while step:
			if step.key == key:
				break
			elif step.can_skip() or step.is_completed():
				step = step.get_next_step()
			else:
				step = None
		else:
			# When step is none
			raise ProcessError("Step '{0}' was not found.".format(key))
		
		if step.is_completed() and step.is_definitive():
			raise ProcessError("Step '{0}' is definitive.".format(key))
		
		self.current_step = step
		
	def step_to_latest(self):
		"""
		Moves forward to the latest step that is not completed.
		"""
		step = self.get_first_step()
		while step:
			if step.is_completed():
				next_step = step.get_next_step()
				if next_step:
					step = next_step
					continue
			
			# Step found
			break
				
		if step.is_completed() and step.is_definitive():
			raise ProcessError("Step '{0}' is definitive.".format(key))
		
		self.current_step = step
		
	def feed(self, data, *args, **kwargs):
		"""
		Tries to complete the current step and if so move on to the next step.
		"""
		if self.current_step.complete(data, *args, **kwargs):
			next_step = self.next_step
			if not next_step is None:
				self.current_step = next_step
			return True
		return False
				
	def render(self, request, *args, **kwargs):
		"""
		Renders the current step in this process.
		"""
		return self.current_step.render(request, *args, **kwargs)
		
		
	def get_first_step(self):
		"""
		Should return the first step in this process.
		"""
		raise NotImplementedError()
	
	def get_current_step(self):
		if self._current_step is None:
			step = self.get_first_step()
			if not step:
				raise ValueError()
			self._current_step = step
		return self._current_step
		
	def set_current_step(self, value):
		if not value:
			raise ValueError()
		self._current_step = value
		self._current_step.hookup(self)
	
	current_step = property(get_current_step, set_current_step)
		
	@property
	def next_step(self):
		if self.current_step:
			step = self.current_step.get_next_step()
			if step:
				step.hookup(self)
			return step
		return None
		
	@property
	def previous_step(self):
		if self.current_step:
			step = self.current_step.get_previous_step()
			if step:
				step.hookup(self)
			return step
		return None
		
	@property
	def completed(self):
		return self.current_step.is_completed() and self.next_step is None
		
	def resolve_url(self, step):
		"""
		Resolves the url for the given step
		"""
		raise NotImplementedError()	
#

class ProcessStep(object):
	
	key = None
	process = None
	
	def __init__(self, key=None):
		if key:
			self.key = key
		if self.key is None:
			raise ValueError("Key for this step is not given.")
			
	def hookup(self, process):
		self.process = process
			
	@property
	def url(self):
		return self.resolve_url()
		
	def is_completed(self):
		"""
		Indicates if this step is completed successfully.
		"""
		raise NotImplementedError()
	
	def can_skip(self):
		"""
		Indicates if this step can be visited again.
		"""
		return False
		
	def is_definitive(self):
		"""
		Indicates if this step can be visited again.
		"""
		return False
		
	def complete(self, request, data, *args, **kwargs):
		"""
		Attempts to complete this step with the given data.
		"""
		raise NotImplementedError()
		
	def render(self, request, *args, **kwargs):
		"""
		Renders this step in it's current state.
		"""
		raise NotImplementedError()
	
	def resolve_url(self):
		"""
		Resolves the url for this step.
		"""
		return self.process.resolve_url(self)
		
	def get_next_step(self):
		"""
		Returns the next step (if any).
		"""
		return None
		
	def get_previous_step(self):
		"""
		Returns the previous step (if any).
		"""
		return None