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
from sellmo.api.decorators import view, chainable, link, context_processor
from sellmo.api.exceptions import ViewNotImplemented
from sellmo.api.configuration import define_import, define_setting
from sellmo.api.messaging import FlashMessages
from sellmo.contrib.account.models import User

from django.http import Http404
from django.core.exceptions import ObjectDoesNotExist
from django.conf import settings
from django.shortcuts import redirect
from django.contrib.auth import (login as auth_login,
                                 logout as auth_logout)


class AccountModule(sellmo.Module):
   
    namespace = 'account'
    
    User = User
    
    allow_get_logout = define_setting(
        'ALLOW_GET_LOGOUT',
        default=False
    )
    
    UserChangeForm = define_import(
        'USER_CHANGE_FORM',
        default='sellmo.contrib.account.forms.UserChangeForm')
    
    UserCreationForm = define_import(
        'USER_CREATION_FORM',
        default='sellmo.contrib.account.forms.UserCreationForm')
        
    AuthenticationForm = define_import(
        'AUTHENTICATION_FORM',
        default='django.contrib.auth.forms.AuthenticationForm')
    
    PasswordResetForm = define_import(
        'PASSWORD_RESET_FORM',
        default='django.contrib.auth.forms.PasswordResetForm')
        
    @context_processor()
    def login_form_context(self, chain, request, context, **kwargs):
        if 'login_form' not in context:
            user, form, processed = self.process_login(request=request)
            context['login_form'] = form
        return chain.execute(request=request, context=context, **kwargs)
    
    @view(r'^login/$')
    def login(self, chain, request, context=None, next=None, 
              invalid='account.login', messages=None, **kwargs):
                
        if messages is None:
            messages = FlashMessages()

        if next is None:
            next = settings.LOGIN_REDIRECT_URL
        
        next = request.POST.get(
            'next', request.GET.get('next', next))
        invalid = request.POST.get(
            'invalid', request.GET.get('invalid', invalid))
        if context is None:
            context = {}
        
        data = None
        if request.method == 'POST':
            data = request.POST
        
        user, form, processed = self.process_login(request=request, data=data)
        context['form'] = form
        
        redirection = None
        if processed:
            self.login_user(request=request, user=user)
            redirection = redirect(next)
        elif data and invalid != 'account.login':
            # We don't want to redirect to ourselves
            redirection = redirect(invalid)
        
        if chain:
            return chain.execute(
                request, user=user, form=form, processed=processed,
                context=context, next=next, invalid=invalid,
                redirection=redirection, messages=messages, **kwargs)
        elif redirection:
            messages.transmit()
            return redirection
        else:
            raise ViewNotImplemented
            
    @chainable()
    def login_user(self, chain, request, user, **kwargs):
        auth_login(request, user)
        if chain:
            chain.execute(request=request, user=user, **kwargs)
        
    @chainable()
    def process_login(self, chain, request, prefix=None, data=None, 
                      user=None, **kwargs):
        
        processed = False
        form = self.AuthenticationForm(request, data=data, prefix=prefix)
       
        if data and form.is_valid():
            processed = True
            if user is None:
                user = form.get_user()
                
            # make sure this user is a customer
            try:
                processed = user.customer is not None
            except ObjectDoesNotExist:
                processed = False
        
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

    @view(r'^logout/$')
    def logout(self, chain, request, context=None, next=None, **kwargs):
        if next is None:
            next = 'account.login'
        
        next = request.POST.get(
            'next', request.GET.get('next', next))
        
        customer = modules.customer.get_customer(request=request)
        if not customer or not customer.is_authenticated():
            raise Http404
            
        user = customer.user
        redirection = None
        processed = False
        
        if request.method == 'POST' or self.allow_get_logout:
            self.logout_user(request=request, user=user)
            processed = True
            redirection = redirect(next)
        
        if chain:
            return chain.execute(
                request, user=user, context=context,
                redirection=redirection, **kwargs)
        elif processed:
            return redirection
        else:
            raise ViewNotImplemented
        
    @chainable()
    def logout_user(self, chain, request, user, **kwargs):
        auth_logout(request)
        if chain:
            chain.execute(request=request, user=user, **kwargs)