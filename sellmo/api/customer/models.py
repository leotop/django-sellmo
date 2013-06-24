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
from sellmo.utils.sessions import TrackingManager

#

@load(after='finalize_customer_Customer')
def load_model():
    class Address(modules.customer.Address):
        customer = models.ForeignKey(
            modules.customer.Customer,
            related_name = 'addresses',
            verbose_name = _("customer")
        )
        
        class Meta:
            abstract = True
        
    modules.customer.Address = Address

@load(after='finalize_customer_Addressee', before='finalize_customer_Customer')
def load_model():
    class Customer(modules.customer.Customer, modules.customer.Addressee):
        class Meta:
            abstract = True
        
    modules.customer.Customer = Customer
    
@load(after='finalize_customer_Addressee', before='finalize_customer_Address')
def load_model():
    class Address(modules.customer.Address, modules.customer.Addressee):
        class Meta:
            abstract = True
        
    modules.customer.Address = Address
        
@load(action='finalize_customer_Customer')
def finalize_model():
    class Customer(modules.customer.Customer):
        class Meta:
            verbose_name = _("customer")
            verbose_name_plural = _("customers")
            
    modules.customer.Customer = Customer
    
@load(action='finalize_customer_Address')
def finalize_model():
    class Address(modules.customer.Address):
        class Meta:
            verbose_name = _("address")
            verbose_name_plural = _("addresses")
    modules.customer.Address = Address

class Addressee(models.Model):

    first_name = models.CharField(
        max_length = 30,
        verbose_name = _("first name")
    )
    
    last_name = models.CharField(
        max_length = 30,
        verbose_name = _("last name")
    )
    
    class Meta:
        app_label = 'customer'
        abstract = True

class Customer(models.Model):
    
    objects = TrackingManager('sellmo_customer')
    
    user = models.OneToOneField(
        User,
        blank = True,
        null = True,
        verbose_name = _("user")
    )
    
    class Meta:
        app_label = 'customer'
        ordering = ['last_name', 'first_name']
        abstract = True
    
class Address(models.Model):
    
    type = models.CharField(
        max_length = 30,
        verbose_name = _("type")
    )
    
    class Meta:
        app_label = 'customer'
        ordering = ['last_name', 'first_name']
        abstract = True