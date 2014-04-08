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

from collections import deque

#

from sellmo.magic import singleton

#


class Loadable(object):

    def __init__(self, func):
        self.func = func
        self.action = []
        self.after = []
        self.before = []
        self._directly_before = None
        self._directly_after = None

    def get_directly_before(self):
        return self._directly_before

    def set_directly_before(self, value):
        if self._directly_before:
            raise Exception("Directly before was already given.")
        self._directly_before = value

    directly_before = property(get_directly_before, set_directly_before)

    def get_directly_after(self):
        return self._directly_after

    def set_directly_after(self, value):
        if self._directly_after:
            raise Exception("Directly after was already given.")
        self._directly_after = value

    directly_after = property(get_directly_after, set_directly_after)

    def __repr__(self):
        return '%s.%s' % (self.func.__module__, self.func.__name__)
#


@singleton
class Loader(object):

    def __init__(self):
        self._queue = deque()
        self._mapping = {}

    def register(self, func, action=None, after=None, before=None, directly=False):

        if self._mapping.has_key(str(func)):
            loadable = self._mapping[str(func)]
        else:
            loadable = Loadable(func)
            self._mapping[str(func)] = loadable
            self._queue.append(loadable)

        if action:
            loadable.action.append(action)
        if after:
            loadable.after.append(after)
        if before:
            loadable.before.append(before)

        if directly:
            if before:
                loadable.directly_before = before

            if after:
                loadable.directly_after = after

    def load(self):

        # Remove references
        self._mapping = {}

        #
        actions = {}
        delays = {}
        executions = deque()
        delayed = deque()

        #
        loadables = self._queue

        # Map actions
        for loadable in loadables:

            if not loadable.action:
                loadable.action.append(str(loadable.func))

            for action in loadable.action:
                if not actions.has_key(action):
                    actions[action] = []
                actions[action].append(loadable)

        # Convert before's to after's
        for loadable in loadables:
            for before in loadable.before:
                directly = loadable.directly_before == before
                if actions.has_key(before):
                    for action in actions[before]:
                        action.after.extend(loadable.action)
                        if directly:
                            action.directly_after = loadable.action[0]

        # Seperate non delayed loadables from delayed loadables
        while loadables:
            loadable = loadables.popleft()
            for delay in loadable.after:
                if not delays.has_key(delay):
                    delays[delay] = []
                delays[delay].append(loadable)

            if not loadable.after:
                # loadable has no delays, append to execution queue
                executions.append(loadable)
            else:
                delayed.append(loadable)

        # Seperate unnecessarily delayed loadables from valid delayed loadables
        loadables = delayed
        delayed = deque()

        while loadables:
            loadable = loadables.popleft()
            for delay in loadable.after:
                if actions.has_key(delay):
                    delayed.append(loadable)
                    break
            else:
                executions.append(loadable)

        # Begin execution
        while executions:
            execution = executions.popleft()

            # Execute
            execution.func()

            # Remove from actions
            for action in execution.action:
                actions[action].remove(execution)
                if not actions[action]:
                    del actions[action]

            # Find loadables for (re)evaluation
            evaluations = deque()
            for action in execution.action:
                if delays.has_key(action):
                    for loadable in delays[action]:
                        if loadable in delayed and not loadable in evaluations:
                            evaluations.append(loadable)

            # (Re-)evaluate loadables
            while evaluations:
                loadable = evaluations.popleft()
                for delay in loadable.after:
                    if actions.has_key(delay):
                        if loadable.directly_after and loadable.directly_after != delay:
                            raise Exception("""Will fail to execute '%s' directly after '%s' due to '%s'""" % (
                                loadable, loadable.directly_after, delay))

                        # Still another delay > DO NOTHING
                        break
                else:
                    # No more valid delays > EXECUTE
                    delayed.remove(loadable)
                    if loadable.directly_after:
                        executions.appendleft(loadable)
                    else:
                        executions.append(loadable)

        # Verify for remaining delays
        if delayed:
            raise Exception("""Failed to load""")

loader = Loader()
