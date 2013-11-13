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
from django.contrib.auth import login as auth_login, logout as auth_logout, authenticate, get_user_model
from django.contrib.auth.forms import AuthenticationForm, PasswordResetForm, SetPasswordForm, PasswordChangeForm, UserCreationForm
from django.contrib.auth.decorators import login_required
from django.views.decorators.debug import sensitive_post_parameters
from django.views.decorators.cache import never_cache
from django.views.decorators.csrf import csrf_protect
from django.utils.decorators import method_decorator

#

import sellmo
from sellmo import modules
from sellmo.api.decorators import view, chainable, link
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
    def get_user_form(self, chain, prefix=None, data=None, user=None, form=None, **kwargs):
        if form is None:
            form = self.UserCreationForm(data, prefix=prefix, instance=user)
        if chain:
            out = chain.execute(prefix=prefix, data=data, form=form, **kwargs)
            form = out.get('form', form)
        return form
        
    @chainable()
    def get_customer_form(self, chain, prefix=None, data=None, customer=None, form=None, **kwargs):
        if form is None:
            form = self.CustomerForm(data, prefix=prefix, instance=customer)
        if chain:
            out = chain.execute(prefix=prefix, data=data, customer=customer, form=form, **kwargs)
            form = out.get('form', form)
        return form
        
    @chainable()
    def get_contactable_form(self, chain, prefix=None, data=None, contactable=None, form=None, **kwargs):
        if form is None:
            form = self.ContactableForm(data, prefix=prefix, instance=contactable)
        if chain:
            out = chain.execute(prefix=prefix, data=data, contactable=contactable, form=form, **kwargs)
            form = out.get('form', form)
        return form
        
    @chainable()
    def get_address_form(self, chain, prefix=None, data=None, address=None, form=None, **kwargs):
        if form is None:
            form = self.AddressForm(data, prefix=prefix, instance=address)
        if chain:
            out = chain.execute(prefix=prefix, data=data, address=address, form=form, **kwargs)
            form = out.get('form', form)
        return form
        
    @chainable()
    def get_login_form(self, chain, request, prefix=None, data=None, form=None, **kwargs):
        if form is None:
            form = self.AuthenticationForm(request, data, prefix=prefix)
        if chain:
            out = chain.execute(prefix=prefix, data=data, form=form, **kwargs)
            form = out.get('form', form)
        return form
    
    # CUSTOMER LOGIC
    
    @chainable()
    def get_customer(self, chain, request, customer=None, **kwargs):
        user = None
        if request.user.is_authenticated():
            user = request.user
            
        # See if we can relate this user to a customer
        if customer is None and not user is None:
            try:
                customer = user.customer
            except ObjectDoesNotExist:
                pass
        if chain:
            out = chain.execute(request=request, customer=customer, **kwargs)
            customer = out.get('customer', customer)
        return customer
        
        
    @chainable()
    def handle_customer(self, chain, request, prefix=None, data=None, customer=None, **kwargs):
        # Try and get customer from request
        customer = self.get_customer(request=request)
        
        processed = False
        form = self.get_customer_form(prefix=prefix, data=data, customer=customer)
        if data and form.is_valid():
            customer = form.save(commit=False)
            processed = True
        
        if chain:
            out = chain.execute(prefix=prefix, data=data, customer=customer, form=form, processed=processed, **kwargs)
            customer, form, processed = out.get('customer', customer), out.get('form', form), out.get('processed', processed)
        return customer, form, processed
        
    # CONTACTABLE LOGIC
        
    @chainable()
    def handle_contactable(self, chain, prefix=None, data=None, contactable=None, **kwargs):
        
        processed = False
        form = self.get_contactable_form(prefix=prefix, data=data, contactable=contactable)
        if data and form.is_valid():
            contactable = form.save(commit=False)
            processed = True
            
        if chain:
            out = chain.execute(prefix=prefix, data=data, contactable=contactable, form=form, processed=processed, **kwargs)
            contactable, form, processed = out.get('contactable', contactable), out.get('form', form), out.get('processed', processed)
        return contactable, form, processed
        
        
    # ADDRESS LOGIC
        
    @chainable()
    def handle_address(self, chain, type, customer=None, prefix=None, data=None, address=None, **kwargs):
        
        if type not in self.address_types:
            raise ValueError("Invalid address type.")
        
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
            out = chain.execute(request=request, prefix=prefix, data=data, address=address, form=form, processed=processed, **kwargs)
            address, form, processed = out.get('address', address), out.get('form', form), out.get('processed', processed)
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
        if chain:
            out = chain.execute(request=request, prefix=prefix, data=data, user=user, form=form, processed=processed, **kwargs)
            user, form, processed = out.get('user', user), out.get('form', form), out.get('processed', processed)
        return user, form, processed
    
    @method_decorator(csrf_protect)
    @method_decorator(never_cache)
    @view(r'^login/$')
    def login(self, chain, request, context=None, **kwargs):
        
        next = request.GET.get('next', 'customer.account')
        
        if context == None:
            context = {}
        
        data = None
        if request.method == 'POST':
            data = request.POST
            
        user, form, processed = self.handle_login(request=request, data=data)
        context['form'] = form
        
        if self.django_auth_enabled and processed:
            auth_login(request, user)
        
        redirection = redirect(next)
        
        if chain:
            return chain.execute(request, user=user, form=form, processed=processed, context=context, redirection=redirection, **kwargs)
        elif processed:
            return redirection
        else:
            raise Http404
            
    # LOGOUT LOGIC
    
    @method_decorator(csrf_protect)
    @method_decorator(never_cache)
    @view(r'^logout/$')
    def logout(self, chain, request, context=None, **kwargs):
        
        next = request.GET.get('next', 'customer.login')
        
        if context == None:
            context = {}
        
        if self.django_auth_enabled:
            auth_logout(request)
        
        redirection = redirect(next)
        
        if chain:
            return chain.execute(request, context=context, redirection=redirection, **kwargs)
        else:
            return redirection
    
    # REGISTRATION LOGIC
        
    @chainable()
    def handle_user_registration(self, chain, prefix=None, data=None, user=None, **kwargs):
        processed = False
        form = self.get_user_form(prefix=prefix, data=data)
        if data and form.is_valid():
            user = form.save(commit=False)
            processed = True
        
        if chain:
            out = chain.execute(prefix=prefix, data=data, user=user, form=form, processed=processed, **kwargs)
            user, form, processed = out.get('user', user), out.get('form', form), out.get('processed', processed)
        return user, form, processed
    
    @method_decorator(csrf_protect)
    @method_decorator(never_cache)
    @view(r'^registration/$')
    def registration(self, chain, request, context=None, **kwargs):
        
        next = request.GET.get('next', 'customer.login')
        redirection = None
        
        customer = self.get_customer(request=request)
        if customer and customer.pk:
            raise Http404("Already registered")
        
        if context == None:
            context = {}
        
        data = None
        if request.method == 'POST':
            data = request.POST
        
        processed = True
            
        if self.django_auth_enabled:
            user, user_form, user_processed = self.handle_user_registration(data=data)
            context['user_form'] = user_form
            processed &= user_processed
        
        customer, customer_form, customer_processed = self.handle_customer(request=request, data=data)
        context['customer_form'] = customer_form
        processed &= customer_processed
        
        addresses = {}
        for type in self.address_types:
            address, form, address_processed = self.handle_address(request=request, type=type, prefix='{0}_address'.format(type), customer=customer, data=data)
            context['{0}_address_form'.format(type)] = form
            processed &= address_processed
            addresses[type] = address
            
        if processed:
            # Create user, customer and addresses
            if self.django_auth_enabled:
                user.save()
                customer.user = user
            for type in self.address_types:
                address = addresses[type]
                address.save()
                customer.set_address(type, address)
            customer.save()
            
            #
            
            redirection = redirect(next)
        
        if chain:
            return chain.execute(request, customer=customer, context=context, processed=processed, redirection=redirection, **kwargs)  
        elif redirection:
            return redirection
        else:
            # We don't render anything
            raise Http404
        
        
    # ACCOUNT LOGIC
    @view(r'^account/$')
    def account(self, chain, request, customer=None, context=None, **kwargs):
        
        if context == None:
            context = {}
        
        if not customer:
            customer = self.get_customer(request=request)
            
        if not customer or not customer.pk:
            raise Http404("Not a customer")
            
        context['customer'] = customer
        
        if chain:
            return chain.execute(request, customer=customer, context=context, **kwargs)
        else:
            # We don't render anything
            raise Http404
    
    @link(namespace='checkout')
    def get_order(self, request, order=None, **kwargs):
        customer = self.get_customer(request=request)
        if not order is None and not order.pk:
            if customer and customer.pk:
                order = self.Contactable.clone(customer, clone=order)
                for address in modules.customer.address_types:
                    order.set_address(address, customer.get_address(address).clone())
        
        if customer and customer.pk:
            order.customer = customer
        
        return {
            'order' : order
        }
    