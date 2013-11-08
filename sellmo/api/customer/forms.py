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

from django import forms

#

from sellmo import modules
from sellmo.api.decorators import load

#


@load(action='load_customer_CustomerForm', after='finalize_customer_Customer')
def load_form():
    
    _exclude = []
    if modules.customer.django_auth_enabled:
        _exclude.append('user')
        
    for address in modules.customer.address_types:
        _exclude.append('{0}_address'.format(address))
    
    class CustomerForm(forms.ModelForm):
        class Meta:
            model = modules.customer.Customer
            exclude = _exclude
    
    modules.customer.CustomerForm = CustomerForm
    
@load(action='load_customer_ContactableForm', after='finalize_customer_Contactable')
def load_form():
    class ContactableForm(forms.ModelForm):
        class Meta:
            model = modules.customer.Contactable

    modules.customer.ContactableForm = ContactableForm
    
@load(action='load_customer_AddressForm', after='finalize_customer_Address')
def load_form():
    class AddressForm(forms.ModelForm):
        class Meta:
            model = modules.customer.Address
            exclude = ('customer', 'type')

    modules.customer.AddressForm = AddressForm
