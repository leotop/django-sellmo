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

from django.http import Http404
from django.db import transaction
from django.core.urlresolvers import reverse
from django.shortcuts import redirect

from sellmo import modules
from sellmo.core.processing import ProcessError
from sellmo.api.decorators import view, chainable, link
from sellmo.api.exceptions import ViewNotImplemented
from sellmo.api.configuration import define_import


class AccountModule(modules.account):
    
    RegistrationProcess = define_import('REGISTRATION_PROCESS')
    
    @chainable()
    def get_registration_process(self, chain, request, customer, process=None,
                                 **kwargs):
        if process is None:
            process = self.RegistrationProcess(
                customer=customer, request=request)
        if chain:
            out = chain.execute(
                process=process, customer=customer, request=request, **kwargs)
            process = out.get('process', process)
        return process

    @view([r'^registration/step/(?P<step>[-a-zA-Z0-9_]+)/$', r'^registration/$'])
    def registration(self, chain, request, step=None, data=None, customer=None,
                     process=None, context=None, **kwargs):
        
        if context is None:
            context = {}
        
        # Try resolve data
        if data is None and request.method == 'POST':
            data = request.POST
        
        # Retrieve customer from request
        if customer is None:
            customer = modules.customer.get_customer(request=request)
        
        # Create new customer
        if customer is None:
            customer = modules.customer.Customer()
            
        # Now make sure customer isnt already authenticated
        if customer.is_authenticated():
            raise Http404("Already authenticated")
            
        if process is None:
            process = self.get_registration_process(
                request=request, customer=customer)
        
        redirection = None
        
        # Perform atomic transactions at this point
        with transaction.atomic():
            # Move to the appropiate step
            if step:
                try:
                    # Go to the given step
                    process.step_to(step)
                except ProcessError as error:
                    raise Http404(error)
        
                # Feed the process
                if data:
                    if process.feed(data):
                        if not process.completed:
                            redirection = redirect(reverse(
                                'account.registration',
                                kwargs={'step': process.current_step.key}))
            else:
                try:
                    # Go to the latest step
                    process.step_to_latest()
                except ProcessError as error:
                    raise Http404(error)
        
                redirection = redirect(reverse(
                    'account.registration',
                    kwargs={'step': process.current_step.key}))
        
        # See if we completed the process
        if process.completed:
            # Assign last completed order
            order = modules.checkout.get_completed_order(request=request)
            if order is not None:
                order.customer = customer
                order.save()
            
            # Redirect to login view
            redirection = redirect(reverse('account.login'))
        
        if redirection:
            return redirection
        
        # Append to context
        context['customer'] = customer
        context['process'] = process
        
        if chain:
            return chain.execute(
                request=request, step=step, customer=customer,
                process=process, context=context, **kwargs)
        
        try:
            return process.render(request, context=context)
        except ProcessError as error:
            raise Http404(error)
            
    