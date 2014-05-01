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

from sellmo import modules
from sellmo.core.processing import ProcessError
from sellmo.api.exceptions import ViewNotImplemented
from sellmo.api.configuration import define_import
from sellmo.api.decorators import view, chainable, link


class AccountModule(modules.account):
    
    RegistrationProcess = define_import(
        'REGISTRATION_PROCESS',
        default='sellmo.contrib.contrib_account.registration'
                '.simple_registration.SimpleRegistrationProcess')
                
    @chainable()
    def process_user_creation(self, chain, request, prefix=None, data=None, 
                  user=None, **kwargs):
    
        processed = False
        form = self.UserCreationForm(data=data, prefix=prefix)
        
        if data and form.is_valid():
            processed = True
            if user is None:
                user = form.save(commit=False)
        
        if chain:
            out = chain.execute(
                request=request, prefix=prefix, data=data, user=user,
                form=form, processed=processed, **kwargs)
            
            user, form, processed = (
                out.get('user', user),
                out.get('form', form),
                out.get('processed', processed)
            )
        return user, form, processed
    
    @view()
    def information_step(self, chain, request, context=None, **kwargs):
        if context is None:
            context = {}
    
        if chain:
            return chain.execute(request=request, context=context, **kwargs)
        else:
            raise ViewNotImplemented