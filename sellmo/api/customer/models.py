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

from django.db import models
from django.contrib.auth.models import User
from django.utils.translation import ugettext_lazy as _

#

from sellmo import modules
from sellmo.api.decorators import load

#

#
# Customer model
#

@load(before='finalize_customer_Customer', after='finalize_customer_Address')
def load_model():
    for type in modules.customer.address_types:
        name = '{0}_address'.format(type)
        modules.customer.Customer.add_to_class(name, 
            models.ForeignKey(
                modules.customer.Address,
                related_name='+',
            )
        )
@load(after='finalize_customer_Addressee', before='finalize_customer_Customer')
def load_model():
    class Customer(modules.customer.Customer, modules.customer.Addressee):
        class Meta:
            abstract = True
        
    modules.customer.Customer = Customer
    
@load(after='finalize_customer_Contactable', before='finalize_customer_Customer')
def load_model():
    class Customer(modules.customer.Customer, modules.customer.Contactable):
        class Meta:
            abstract = True

    modules.customer.Customer = Customer
        
@load(action='finalize_customer_Customer')
def finalize_model():
    class Customer(modules.customer.Customer):
        
        if modules.customer.django_auth_enabled:
            user = models.OneToOneField(
                User,
                editable = False,
                verbose_name = _("user"),
                related_name = 'customer'
            )
        
        class Meta:
            verbose_name = _("customer")
            verbose_name_plural = _("customers")
            
    modules.customer.Customer = Customer
    
class Customer(models.Model):

    def get_address(self, type):
        return getattr(self, '{0}_address'.format(type))

    def set_address(self, type, value):
        setattr(self, '{0}_address'.format(type), value)

    class Meta:
        app_label = 'customer'
        ordering = ['last_name', 'first_name']
        abstract = True
    
#
# Address model
#
    
@load(after='finalize_customer_Addressee', before='finalize_customer_Address')
def load_model():
    class Address(modules.customer.Address, modules.customer.Addressee):
        class Meta:
            abstract = True

    modules.customer.Address = Address
    
@load(action='finalize_customer_Address')
def finalize_model():
    class Address(modules.customer.Address):
        class Meta:
            verbose_name = _("address")
            verbose_name_plural = _("addresses")
    
    modules.customer.Address = Address
    
class Address(models.Model):

    class Meta:
        app_label = 'customer'
        ordering = ['last_name', 'first_name']
        abstract = True
    
#
# Contactable model
#

@load(action='finalize_customer_Contactable')
def finalize_model():
    class Contactable(modules.customer.Contactable):
        
        email = models.EmailField(
            blank = not modules.customer.email_required,
            verbose_name = _("email address"),
        )
        
        class Meta:
            abstract = True

    modules.customer.Contactable = Contactable
    
class Contactable(models.Model):
    
    class Meta:
        app_label = 'customer'
        abstract = True
  
#
# Addressee model
#  

@load(action='finalize_customer_Addressee')
def finalize_model():
    class Addressee(modules.customer.Addressee):
        
        if modules.customer.businesses_allowed:
            company_name = models.CharField(
                max_length = 50,
                verbose_name = _("company name"),
                blank = not modules.customer.businesses_only,
            )
            @property
            def is_business(self):
                return bool(self.company_name)
        else:
            @property
            def is_business(self):
                return False
        
        class Meta:
            abstract = True

    modules.customer.Addressee = Addressee     

class Addressee(models.Model):

    first_name = models.CharField(
        max_length = 30,
        verbose_name = _("first name")
    )
    
    last_name = models.CharField(
        max_length = 30,
        verbose_name = _("last name")
    )
    
    def __unicode__(self):
        return u"{0} {1}".format(self.first_name, self.last_name)
    
    class Meta:
        app_label = 'customer'
        abstract = True
