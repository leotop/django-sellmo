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


from sellmo import modules
from sellmo.contrib.account.registration \
           .process import (RegistrationProcess,
                            RegistrationStep)


class SimpleRegistrationProcess(RegistrationProcess):
    def get_first_step(self):
        return InformationStep(customer=self.customer, request=self.request)

class InformationStep(RegistrationStep):
    key = 'information'
    invalid_context = None

    def is_completed(self):
        return self.customer.pk is not None

    def contextualize_or_complete(self, request, context, data=None,
                                  success=True):
        addresses = {}
        
        user, form, processed = modules.account.process_user_creation(
            request=request, prefix='user', data=data)
        context['user_form'] = form
        success &= processed
    
        customer, form, processed = modules.customer.process_customer(
            request=request, prefix='customer',
            customer=self.customer, data=data)
        context['customer_form'] = form
        success &= processed
    
        for type in modules.customer.address_types:
            address, form, processed = modules.customer.process_address(
                request=request, type=type,
                prefix='{0}_address'.format(type),
                address=self.customer.get_address(type), data=data)
            context['{0}_address_form'.format(type)] = form
            success &= processed
            addresses[type] = address
    
        if data is not None and success:
            user.save()
            for type in modules.customer.address_types:
                address = addresses[type]
                address.save()
                self.customer.set_address(type, address)
            self.customer.user = user
            self.customer.save()
    
        return success
    
    def complete(self, data):
        self.invalid_context = {}
        return self.contextualize_or_complete(
            self.request, self.invalid_context, data)
    
    def render(self, request, context):
        if self.invalid_context is None:
            self.contextualize_or_complete(request, context)
        else:
            context.update(self.invalid_context)
    
        return modules.account.information_step(
            request=request, context=context)