# Copyright (c) 2014, Adaptiv Design
# All rights reserved.
# 
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:

# 1. Redistributions of source code must retain the above copyright notice,
# this list of conditions and the following disclaimer.

# 2. Redistributions in binary form must reproduce the above copyright notice,
# this list of conditions and the following disclaimer in the documentation
# and/or other materials provided with the distribution.

# 3. Neither the name of the copyright holder nor the names of its contributors
# may be used to endorse or promote products derived from this software without
# specific prior written permission.

# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
# ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE
# LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR
# CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF
# SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS
# INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN
# CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)
# ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
# POSSIBILITY OF SUCH DAMAGE.


from collections import OrderedDict

from sellmo.utils.sorting import topological_sort


class Loadable(object):
    
    def __init__(self, func=None, action=None):
        self.func = func
        self.action = action
        
    def __eq__(self, other):
        return hash(self) == hash(other)
        
    def __hash__(self):
        if self.func:
            return hash(self.func)
        return hash(self.action)
        
    def __repr__(self):
        if self.func and self.action:
            return ("{0}.{1} ({2})"
                    .format(self.func.__module__,
                            self.func.__name__,
                            self.action))
        if self.func:
            return ("{0}.{1}"
                    .format(self.func.__module__,
                            self.func.__name__))
        return self.action
        

class Loader(object):
    
    def __init__(self):
        self._graph = OrderedDict()
        self._actions = dict() # Maps actions to loadables

    def _register_placeholder(self, action):
        loadable = Loadable(action=action)
        self._graph[loadable] = []
        self._actions[action] = loadable
        return loadable

    def register(self, func, action=None, after=None, before=None):
        loadable = Loadable(func, action)
        if func not in self._graph and action not in self._graph:
            # No existing entry, create dependency list
            self._graph[loadable] = []
        
        if action is not None:
            # Make sure this action is not
            # yet registered.
            if (action in self._actions):
                # A loadable is already present for this
                # action. Make sure loadable has no function
                # assigned.
                if self._actions[action].func:
                    raise Exception("A function is already registered"
                                    " as action '{0}".format(action))
                # We can now assign the actual function to 
                # the placeholder loadable. This can occur
                # if dependencies are registered before this
                # loadable was defined.
                self._graph[loadable] = self._graph.pop(action)
                self._actions[action].func = func
            else:
                # Map loadable to action now that it's given
                self._actions[action] = loadable
            
        # Handle after and before, first make sure a loadable is 
        # present. If not create a placeholder loadable.  
        if after is not None:
            after = (self._register_placeholder(after) if 
                     after not in self._actions else self._actions[after])
            self._graph[loadable].append(after)
            
        if before is not None:
            before = (self._register_placeholder(before) if 
                      before not in self._actions else self._actions[before])
            self._graph[before].append(loadable)

    def load(self):
        for loadable in topological_sort(self._graph):
            if loadable.func:
                loadable.func()
            