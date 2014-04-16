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
from sellmo.api.configuration import setting, class_setting
from sellmo.api.decorators import view, chainable, link
from sellmo.api.customer.models import (Addressee,
                                        Address,
                                        Contactable,
                                        Customer)


class CustomerModule(sellmo.Module):

    namespace = 'customer'
    prefix = 'customer'
    enabled = True

    Addressee = Addressee
    Address = Address
    Contactable = Contactable
    Customer = Customer

    CustomerForm = class_setting(
        'CUSTOMER_FORM',
        default='sellmo.api.customer.forms.CustomerForm')
        
    ContactableForm = class_setting(
        'CONTACTABLE_FORM',
        default='sellmo.api.customer.forms.ContactableForm')
        
    AddressForm = class_setting(
        'ADDRESS_FORM',
        default='sellmo.api.customer.forms.AddressForm')
        
    address_types = setting(
        'ADDRESS_TYPES',
        default=['shipping', 'billing']
    )
    
    auth_enabled = setting(
        'AUTH_ENABLED',
        default=True
    )
    
    customer_required = setting(
        'CUSTOMER_REQUIRED',
        default=False
    )
    
    email_required = setting(
        'EMAIL_REQUIRED',
        default=True
    )
    
    businesses_only = setting(
        'BUSINESSES_ONLY',
        default=False
    )
    
    businesses_allowed = setting(
        'BUSINESSES_ALLOWED',
        default=True
    )
    
    def __init__(self):
        pass

    # Forms

    @chainable()
    def get_customer_form(self, chain, prefix=None, data=None, customer=None,
                          form=None, **kwargs):
        if form is None:
            form = self.CustomerForm(data, prefix=prefix, instance=customer)
        if chain:
            out = chain.execute(
                prefix=prefix, data=data,
                customer=customer, form=form, **kwargs)
            form = out.get('form', form)
        return form

    @chainable()
    def get_contactable_form(self, chain, prefix=None, data=None,
                             contactable=None, form=None, **kwargs):
        if form is None:
            form = self.ContactableForm(
                data, prefix=prefix, instance=contactable)
        if chain:
            out = chain.execute(
                prefix=prefix, data=data,
                contactable=contactable, form=form, **kwargs)
            form = out.get('form', form)
        return form

    @chainable()
    def get_address_form(self, chain, prefix=None, data=None, address=None, 
                         form=None, **kwargs):
        if form is None:
            form = self.AddressForm(data, prefix=prefix, instance=address)
        if chain:
            out = chain.execute(
                prefix=prefix, data=data, address=address, form=form, **kwargs)
            form = out.get('form', form)
        return form

    @chainable()
    def process_customer(self, chain, request, prefix=None, data=None,
                         customer=None, **kwargs):
        # Try and get customer from request
        customer = self.get_customer(request=request)

        processed = False
        form = self.get_customer_form(
            prefix=prefix, data=data, customer=customer)
        
        if data and form.is_valid():
            customer = form.save(commit=False)
            processed = True

        if chain:
            out = chain.execute(
                request=request, prefix=prefix, data=data,
                customer=customer, form=form, processed=processed, **kwargs)
            customer, form, processed = (
                out.get('customer', customer),
                out.get('form', form),
                out.get('processed', processed))
        return customer, form, processed
    
    @chainable()
    def process_contactable(self, chain, request, prefix=None, data=None,
                            contactable=None, **kwargs):
        processed = False
        form = self.get_contactable_form(
            prefix=prefix, data=data, contactable=contactable)
        
        if data and form.is_valid():
            contactable = form.save(commit=False)
            processed = True

        if chain:
            out = chain.execute(
                request=request, prefix=prefix, data=data,
                contactable=contactable, form=form, processed=processed,
                **kwargs)
            contactable, form, processed = (
                out.get('contactable', contactable),
                out.get('form', form),
                out.get('processed', processed)
            )
        return contactable, form, processed
    
    @chainable()
    def process_address(self, chain, request, type, customer=None,
                        prefix=None, data=None, address=None, **kwargs):
        
        if type not in modules.customer.address_types:
            raise ValueError("Invalid address type.")

        # See if we can resolve an existing address from customer
        if address is None and customer:
            address = customer.get_address(type)

        processed = False
        form = self.get_address_form(
            type=type, prefix=prefix, data=data, address=address)
        if data and form.is_valid():
            address = form.save(commit=False)
            address.type = type
            address.customer = customer
            processed = True

        if chain:
            out = chain.execute(
                request=request, prefix=prefix, data=data, address=address, 
                form=form, processed=processed, **kwargs)
            address, form, processed = (
                out.get('address', address),
                out.get('form', form),
                out.get('processed', processed)
            )
        return address, form, processed

    @chainable()
    def get_customer(self, chain, request, customer=None, **kwargs):
        if self.auth_enabled:
            user = None
            if request.user.is_authenticated():
                user = request.user
            # See if we can relate this user to a customer
            if customer is None and not user is None:
                try:
                    customer = user.customer
                except self.customer.DoesNotExist:
                    pass
        if chain:
            out = chain.execute(request=request, customer=customer, **kwargs)
            customer = out.get('customer', customer)
        return customer

    @link(namespace='checkout')
    def get_order(self, request, order=None, **kwargs):
        customer = self.get_customer(request=request)
        if not order is None and not order.pk:
            if customer and customer.pk:
                order = self.Contactable.clone(customer, clone=order)
                for address in modules.customer.address_types:
                    order.set_address(
                        address, customer.get_address(address).clone())

        if customer and customer.pk:
            order.customer = customer

        return {
            'order': order
        }
