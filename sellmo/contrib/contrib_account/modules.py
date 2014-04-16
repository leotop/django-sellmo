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


import sellmo
from sellmo import modules
from sellmo.api.decorators import view, chainable, link
from sellmo.api.configuration import class_setting
from sellmo.contrib.contrib_account.models import User
from sellmo.contrib.contrib_account.forms import (UserChangeForm,
                                                  UserCreationForm)

from django.http import Http404
from django.shortcuts import redirect
from django.contrib.auth import (login as auth_login,
                                 logout as auth_logout)


class AccountModule(sellmo.Module):
    namespace = 'account'
    
    User = User
    
    UserChangeForm = class_setting(
        'USER_CHANGE_FORM',
        default='sellmo.contrib.contrib_account.forms.UserChangeForm')
    
    UserCreationForm = class_setting(
        'USER_CREATION_FORM',
        default='sellmo.contrib.contrib_account.forms.UserCreationForm')
        
    AuthenticationForm = class_setting(
        'AUTHENTICATION_FORM',
        default='django.contrib.auth.forms.AuthenticationForm')
    
    PasswordResetForm = class_setting(
        'PASSWORD_RESET_FORM',
        default='django.contrib.auth.forms.PasswordResetForm')
    
    RegistrationProcess = class_setting(
        'REGISTRATION_PROCESS',
        default='sellmo.contrib.contrib_account')
    
    @view(r'^login$')
    def login(self, chain, request, context=None, **kwargs):
        next = request.GET.get('next', 'account.profile')
        if context is None:
            context = {}
        
        data = None
        if request.method == 'POST':
            data = request.POST
        
        user, form, processed = self.process_login(request=request, data=data)
        context['form'] = form
        
        if processed:
            self.login_user(request=request, user=user)
        redirection = redirect(next)
        
        if chain:
            return chain.execute(
                request, user=user, form=form, processed=processed,
                context=context, redirection=redirection, **kwargs)
        elif processed:
            return redirection
        else:
            raise Http404
            
    @chainable()
    def login_user(self, chain, request, user, **kwargs):
        auth_login(request, user)
        if chain:
            chain.execute(request=request, user=user, **kwargs)
        
    @chainable()
    def process_login(self, chain, request, prefix=None, data=None, 
                      user=None, **kwargs):
        processed = False
        form = self.get_login_form(
            request=request, prefix=prefix, data=data)
        if data and form.is_valid():
            processed = True
            if user is None:
                user = form.get_user()
        if chain:
            out = chain.execute(
                request=request, prefix=prefix, data=data, user=user,
                form=form, processed=processed, **kwargs
            )
            user, form, processed = (
                out.get('user', user),
                out.get('form', form),
                out.get('processed', processed)
            )
        return user, form, processed

    @view(r'^logout$')
    def logout(self, chain, request, context=None, **kwargs):
        raise Http404
        
    @chainable()
    def logout_user(self, chain, request, user, **kwargs):
        auth_logout(request)
        if chain:
            chain.execute(request=request, user=user, **kwargs)
        
    @view(r'^profile$')
    def profile(self, chain, request, context=None, **kwargs):
        raise Http404
        
    @view(r'^registration$')
    def registration(self, chain, request, context=None, **kwargs):
        raise Http404