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


from django.utils.translation import ugettext_lazy as _
from django.utils.functional import allow_lazy


ORDER_EVENTS = [
    'on_pending',
    'on_completed',
    'on_canceled',
    'on_closed',
    'on_paid'
]


ORDER_STATUSES = {
    'new': (_("New"), {
        'initial': True,
        'flow': ['awaiting_payment', 'processing', 'completed', 'canceled'],
        'state': 'new',
    }),
    'awaiting_payment': (_("Awaiting payment"), {
        'flow': ['canceled', 'payment_received'],
        'on_pending': True,
        'state': 'pending',
    }),
    'payment_received': (_("Payment received"), {
        'flow': ['processing'],
        'on_paid': True,
        'state': 'pending',
    }),
    'processing': (_("Processing"), {
        'flow': ['canceled', 'completed', 'on_hold'],
        'state': 'pending',
    }),
    'on_hold': (_("On hold"), {
        'flow': ['processing', 'completed'],
        'state': 'pending',
    }),
    'completed': (_("Completed"), {
        'flow': ['closed', 'shipped'],
        'state': 'completed',
        'on_completed': True,
    }),
    'shipped': (_("Shipped"), {
        'flow': ['closed'],
        'state': 'completed',
    }),
    'canceled': (_("Canceled"), {
        'state': 'canceled',
        'on_canceled': True,
    }),
    'closed': (_("Closed"), {
        'state': 'closed',
        'on_closed': True,
    }),
}


class OrderStatusesHelper(dict):
    
    def __init__(self, *args, **kwargs):
        super(OrderStatusesHelper, self).__init__(*args, **kwargs)
        initial = None
        choices = []
        event_to_status = {}
        status_to_state = {}
        
        for status, entry in self.iteritems():
            config = entry[1] if len(entry) == 2 else {}
            if 'initial' in config and config['initial']:
                if initial is not None:
                    raise ValueError("Only one order status can be "
                                     "defined as initial.")
                initial = status
            if 'state' in config:
                status_to_state[status] = config['state']
            if 'flow' in config:
                # Check flow
                for allowed in config['flow']:
                    if allowed not in self:
                        raise ValueError(
                            "Order status '{0}' does not "
                            "exist.".format(allowed))
            for event in ORDER_EVENTS:
                if event in config:
                    if event in event_to_status:
                        raise ValueError(
                            "Can only have one status "
                            "responding to '{0}'.".format(event))
                    event_to_status[event] = status
        
            choices.append((status, entry[0]))
            
        if not initial:
            raise ValueError("No initial order status configured.")
            
        self.initial = initial
        self.choices = choices
        self.event_to_status = event_to_status
        self.status_to_state = status_to_state
            
        
