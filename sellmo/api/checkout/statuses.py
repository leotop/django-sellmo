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

from sellmo import modules
from sellmo.config import settings

#

__all__ = [
	'initial_status',
	'status_choices',
	'status_events',
	'status_states',
]

#

events = ['on_pending', 'on_completed', 'on_canceled', 'on_closed', 'on_paid']
initial_status = None
status_choices = []
status_events = {}
status_states = {}

# Validate order statuses and hookup events
for status, entry in settings.ORDER_STATUSES.iteritems():
	config = entry[1] if len(entry) == 2 else {}
	if 'initial' in config and config['initial']:
		if initial_status is not None:
			raise Exception("Only one order status can be defined as initial.")
		initial_status = status
	if 'state' in config:
		status_states[status] = config['state'] 
	if 'flow' in config:
		# Check flow
		for allowed in config['flow']:
			if allowed not in settings.ORDER_STATUSES:
				raise Exception("Order status '{0}' does not exist.".format(allowed))
	for event in events:
		if event in config:
			if event in status_events:
			   raise Exception("Can only have one status responding to '{0}'.".format(event))
			status_events[event] = status

	status_choices.append((status, entry[0]))

# Validate
if not initial_status:
	raise Exception("No initial order status configured.")