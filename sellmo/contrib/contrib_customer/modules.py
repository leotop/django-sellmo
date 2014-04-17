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
from sellmo.api.configuration import define_setting

from django.utils.translation import ugettext_lazy as _


class CustomerModule(modules.customer):
    
    phone_number_enabled = define_setting(
        'PHONE_NUMBER_ENABLED',
        default=True)
        
    phone_number_required = define_setting(
        'PHONE_NUMBER_REQUIRED',
        default=False)
    
    name_prefix_enabled = define_setting(
        'NAME_PREFIX_ENABLED',
        default=False)
    
    name_prefix_required = define_setting(
        'NAME_PREFIX_REQUIRED',
        default=True)
    
    name_prefix_choices = define_setting(
        'NAME_PREFIX_CHOICES',
        default=[
            ('sir', _("sir")),
            ('madame', _("madam")),
        ])
        
    name_suffix_enabled = define_setting(
        'NAME_SUFFIX_ENABLED',
        default=True)
    
    
    """
    
    @method_decorator(csrf_protect)
    @method_decorator(never_cache)
    @view(r'^login/$')
    def login(self, chain, request, context=None, **kwargs):
        next = request.GET.get('next', 'customer.account')
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
    
    # LOGOUT LOGIC
    
    @method_decorator(csrf_protect)
    @method_decorator(never_cache)
    @view(r'^logout/$')
    def logout(self, chain, request, context=None, **kwargs):
        next = request.GET.get('next', 'customer.login')
        if context is None:
            context = {}
    
        self.logout_user(request=request, user=request.user)
        redirection = redirect(next)
    
        if chain:
            return chain.execute(
                request, context=context, redirection=redirection, **kwargs)
        else:
            return redirection
    
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
    
    @chainable()
    def logout_user(self, chain, request, user, **kwargs):
        if modules.customer.auth_enabled:
            auth_logout(request)
        if chain:
            chain.execute(request=request, user=user, **kwargs)
            
    @chainable()
    def login_user(self, chain, request, user, **kwargs):
        if modules.customer.auth_enabled:
            auth_login(request, user)
        if chain:
            chain.execute(request=request, user=user, **kwargs)
            
    @chainable()
    def process_user_creation(self, chain, request, prefix=None,
                              data=None, user=None, **kwargs):
        
        processed = False
        form = self.get_user_form(prefix=prefix, data=data)
        if data and form.is_valid():
            user = form.save(commit=False)
            processed = True
    
        if chain:
            out = chain.execute(
                request=request, prefix=prefix, data=data,
                user=user, form=form, processed=processed, **kwargs)
            user, form, processed = (
                out.get('user', user),
                out.get('form', form),
                out.get('processed', processed))
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
    
        if context is None:
            context = {}
    
        data = None
        if request.method == 'POST':
            data = request.POST
    
        processed = True
    
        if modules.customer.auth_enabled:
            user, user_form, user_processed = self.process_user_creation(
                request=request, data=data)
            context['user_form'] = user_form
            processed &= user_processed
    
        customer, customer_form, customer_processed = self.process_customer(
            request=request, data=data)
        context['customer_form'] = customer_form
        processed &= customer_processed
    
        addresses = {}
        for type in modules.customer.address_types:
            address, form, address_processed = self.process_address(
                request=request, type=type, 
                prefix='{0}_address'.format(type), 
                customer=customer, data=data)
            context['{0}_address_form'.format(type)] = form
            processed &= address_processed
            addresses[type] = address
    
        if processed:
            # Create user, customer and addresses
            if modules.customer.auth_enabled:
                user.save()
                customer.user = user
            for type in modules.customer.address_types:
                address = addresses[type]
                address.save()
                customer.set_address(type, address)
    
            customer.save()
            redirection = redirect(next)
    
        if chain:
            return chain.execute(
                request, customer=customer, context=context,
                processed=processed, redirection=redirection, **kwargs)
        elif redirection:
            return redirection
        else:
            # We don't render anything
            raise Http404
    
    # ACCOUNT LOGIC
    
    @view(r'^account/$')
    def account(self, chain, request, customer=None, context=None, **kwargs):
        if context is None:
            context = {}
    
        if not customer:
            customer = self.get_customer(request=request)
        if not customer or not customer.pk:
            raise Http404("Not a customer")
    
        context['customer'] = customer
    
        if chain:
            return chain.execute(
                request, customer=customer, context=context, **kwargs)
        else:
            # We don't render anything
            raise Http404
    """