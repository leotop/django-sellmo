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

from django.http import Http404
from django.shortcuts import redirect
from django.core.exceptions import ObjectDoesNotExist
from django.contrib.auth import login as auth_login, logout as auth_logout, get_user_model
from django.contrib.auth.forms import AuthenticationForm, PasswordResetForm, SetPasswordForm, PasswordChangeForm, UserCreationForm
from django.contrib.auth.decorators import login_required
from django.views.decorators.debug import sensitive_post_parameters
from django.views.decorators.cache import never_cache
from django.views.decorators.csrf import csrf_protect
from django.utils.decorators import method_decorator

#

import sellmo
from sellmo import modules
from sellmo.api.decorators import view, chainable
from sellmo.api.customer.models import Addressee, Address, Contactable, Customer

# Need this in order for forms to load
from sellmo.api.customer.forms import *

#

class CustomerModule(sellmo.Module):

    namespace = 'customer'
    prefix = 'customer'
    enabled = True
    
    # Model configuration
    address_types = ['shipping', 'billing']
    email_required = True
    businesses_allowed = True
    businesses_only = False
    django_auth_enabled = True
    
    Addressee = Addressee
    Address = Address
    Contactable = Contactable
    Customer = Customer
    
    CustomerForm = None
    ContactableForm = None
    AddressForm = None
    
    # Django Auth forms
    AuthenticationForm = AuthenticationForm
    PasswordResetForm = PasswordResetForm
    SetPasswordForm = SetPasswordForm
    UserCreationForm = UserCreationForm
    PasswordChangeForm = PasswordChangeForm
    
    def __init__(self, *args, **kwargs):        
        pass
        
    # Forms
        
    @chainable()
    def get_user_form(self, chain, request, prefix=None, data=None, user=None, form=None, **kwargs):
        if form is None:
            form = self.UserCreationForm(data, prefix=prefix, instance=user)
        if chain:
            return chain.execute(prefix=prefix, data=data, form=form, **kwargs)
        return form
        
    @chainable()
    def get_customer_form(self, chain, prefix=None, data=None, customer=None, form=None, **kwargs):
        if form is None:
            form = self.CustomerForm(data, prefix=prefix, instance=customer)
        if chain:
            return chain.execute(prefix=prefix, data=data, customer=customer, form=form, **kwargs)
        return form
        
    @chainable()
    def get_contactable_form(self, chain, prefix=None, data=None, contactable=None, form=None, **kwargs):
        if form is None:
            form = self.ContactableForm(data, prefix=prefix, instance=contactable)
        if chain:
            return chain.execute(prefix=prefix, data=data, contactable=contactable, form=form, **kwargs)
        return form
        
    @chainable()
    def get_address_form(self, chain, prefix=None, data=None, address=None, form=None, **kwargs):
        if form is None:
            form = self.AddressForm(data, prefix=prefix, instance=address)
        if chain:
            return chain.execute(prefix=prefix, data=data, address=address, form=form, **kwargs)
        return form
        
    @chainable()
    def get_login_form(self, chain, request, prefix=None, data=None, form=None, **kwargs):
        if form is None:
            form = self.AuthenticationForm(request, data, prefix=prefix)
        if chain:
            return chain.execute(prefix=prefix, data=data, form=form, **kwargs)
        return form
    
    # CUSTOMER LOGIC
        
    @chainable()
    def handle_customer(self, chain, request, prefix=None, data=None, customer=None, **kwargs):
        
        user = None
        if request.user.is_authenticated():
            user = request.user
        
        # See if we can relate this user to a customer
        if customer is None and not user is None:
            try:
                customer = user.customer
            except ObjectDoesNotExist:
                pass
        
        processed = False
        form = self.get_customer_form(prefix=prefix, data=data, customer=customer)
        if data and form.is_valid():
            customer = form.save(commit=False)
            if not user:
                raise Exception("Need a valid user.")
            customer.user = user
            processed = True
            
        if chain:
            return chain.execute(prefix=prefix, data=data, customer=customer, form=form, processed=processed, **kwargs)
        return customer, form, processed
        
    # CONTACTABLE LOGIC
        
    @chainable()
    def handle_contactable(self, chain, request, prefix=None, data=None, contactable=None, **kwargs):
        
        processed = False
        form = self.get_contactable_form(prefix=prefix, data=data, contactable=contactable)
        if data and form.is_valid():
            contactable = form.save(commit=False)
            processed = True
            
        if chain:
            return chain.execute(prefix=prefix, data=data, contactable=contactable, form=form, processed=processed, **kwargs)
        return contactable, form, processed
        
        
    # ADDRESS LOGIC
        
    @chainable()
    def handle_address(self, chain, request, type, prefix=None, data=None, address=None, customer=None, **kwargs):
        
        if type not in self.address_types:
            raise ValueError("Invalid address type.")
        
        # See if we can relate this request to a customer
        if customer is None:
            customer, form, processed = self.handle_customer(request=request)
        
        # See if we can resolve an existing address from customer
        if address is None and customer:
            address = customer.get_address(type)
        
        processed = False
        form = self.get_address_form(type=type, prefix=prefix, data=data, address=address)
        if data and form.is_valid():
            address = form.save(commit=False)
            address.type = type
            address.customer = customer
            processed = True
            
        if chain:
            return chain.execute(request=request, prefix=prefix, data=data, address=address, form=form, processed=processed, **kwargs)
        return address, form, processed
      
    # LOGIN LOGIC
        
    @chainable()
    def handle_login(self, chain, request, prefix=None, data=None, user=None, **kwargs):
        processed = False
        form = self.get_login_form(request=request, prefix=prefix, data=data)
        if data and form.is_valid():
            processed = True
            if user is None:
                user = form.get_user()
        if user:
            auth_login(request, user)
        if chain:
            return chain.execute(request=request, prefix=prefix, data=data, user=user, form=form, processed=processed, **kwargs)
        return user, form, processed
    
    @method_decorator(csrf_protect)
    @method_decorator(never_cache)
    @view(r'^login/$')
    def login(self, chain, request, context=None, **kwargs):
        if context == None:
            context = {}
        
        data = None
        if request.method == 'POST':
            data = request.POST
            
        user, form, processed = self.handle_login(request=request, data=data)
        context['form'] = form
        
        if chain:
            return chain.execute(request, user=user, form=form, processed=processed, context=context, **kwargs)
        else:
            # We don't render anything
            raise Http404
    
    # REGISTRATION LOGIC
        
    @chainable()
    def handle_user_registration(self, chain, request, prefix=None, data=None, user=None, **kwargs):
        processed = False
        form = self.get_user_form(request=request, prefix=prefix, data=data)
        if data and form.is_valid():
            user = form.save(commit=False)
            processed = True
        
        if chain:
            return chain.execute(request=request, prefix=prefix, data=data, user=user, form=form, processed=processed, **kwargs)
        return user, form, processed
    
    @method_decorator(csrf_protect)
    @method_decorator(never_cache)
    @view(r'^registration/$')
    def registration(self, chain, request, context=None, **kwargs):
        if context == None:
            context = {}
        
        data = None
        if request.method == 'POST':
            data = request.POST
            
        user, user_form, processed = self.handle_user_registration(request=request, data=data)
        context['user_form'] = user_form
        
        customer, customer_form, processed = self.handle_customer(request=request, data=data)
        context['customer_form'] = customer_form
        
        for type in self.address_types:
            address, form, processed = self.handle_address(request=request, type=type, prefix='{0}_address'.format(type), data=data)
            context['{0}_address_form'.format(type)] = form
        
        if chain:
            return chain.execute(request, customer=customer, processed=processed, context=context, **kwargs)
        else:
            # We don't render anything
            raise Http404