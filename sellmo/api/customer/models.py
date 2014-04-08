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
from sellmo.config import settings
from sellmo.utils.cloning import Cloneable
from sellmo.api.decorators import load

#

#
# Customer model
#


@load(before='finalize_customer_Customer', after='finalize_customer_Address')
def load_model():
    for type in settings.ADDRESS_TYPES:
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

        class Meta(modules.customer.Customer.Meta):
            abstract = True

    modules.customer.Customer = Customer


@load(after='finalize_customer_Contactable', before='finalize_customer_Customer')
def load_model():
    class Customer(modules.customer.Customer, modules.customer.Contactable):

        class Meta(modules.customer.Customer.Meta):
            abstract = True

    modules.customer.Customer = Customer


@load(action='finalize_customer_Customer')
def finalize_model():
    class Customer(modules.customer.Customer):

        class Meta(modules.customer.Customer.Meta):
            app_label = 'customer'
            verbose_name = _("customer")
            verbose_name_plural = _("customers")

    modules.customer.Customer = Customer


class Customer(models.Model, Cloneable):

    if settings.AUTH_ENABLED:
        user = models.OneToOneField(
            User,
            related_name='customer',
            verbose_name=_("user"),
        )

    def get_address(self, type):
        try:
            return getattr(self, '{0}_address'.format(type))
        except modules.customer.Address.DoesNotExist:
            return None

    def set_address(self, type, value):
        setattr(self, '{0}_address'.format(type), value)

    def clone(self, cls=None, clone=None):
        clone = super(Customer, self).clone(cls=cls, clone=clone)
        if settings.AUTH_ENABLED:
            clone.user = self.user
        return clone

    class Meta:
        ordering = ['last_name', 'first_name']
        abstract = True

#
# Address model
#


@load(after='finalize_customer_Addressee', before='finalize_customer_Address')
def load_model():
    class Address(modules.customer.Address, modules.customer.Addressee):

        class Meta(modules.customer.Address.Meta):
            abstract = True

    modules.customer.Address = Address


@load(action='finalize_customer_Address')
def finalize_model():
    class Address(modules.customer.Address):

        class Meta(modules.customer.Address.Meta):
            app_label = 'customer'
            verbose_name = _("address")
            verbose_name_plural = _("addresses")

    modules.customer.Address = Address


class Address(models.Model, Cloneable):

    def clone(self, cls=None, clone=None):
        clone = super(Address, self).clone(cls=cls, clone=clone)
        return clone

    class Meta:
        ordering = ['last_name', 'first_name']
        abstract = True

#
# Contactable model
#


@load(action='finalize_customer_Contactable')
def finalize_model():
    class Contactable(modules.customer.Contactable):

        email = models.EmailField(
            blank=not settings.EMAIL_REQUIRED,
            verbose_name=_("email address"),
        )

        class Meta(modules.customer.Contactable.Meta):
            abstract = True

    modules.customer.Contactable = Contactable


class Contactable(models.Model, Cloneable):

    def clone(self, cls=None, clone=None):
        clone = super(Contactable, self).clone(cls=cls, clone=clone)
        clone.email = self.email
        return clone

    class Meta:
        abstract = True

#
# Addressee model
#


@load(action='finalize_customer_Addressee')
def finalize_model():
    class Addressee(modules.customer.Addressee):

        if settings.BUSINESSES_ALLOWED:
            company_name = models.CharField(
                max_length=50,
                verbose_name=_("company name"),
                blank=not settings.BUSINESSES_ONLY,
            )

            @property
            def is_business(self):
                return bool(self.company_name)
        else:
            @property
            def is_business(self):
                return False

        class Meta(modules.customer.Addressee.Meta):
            abstract = True

    modules.customer.Addressee = Addressee


class Addressee(models.Model, Cloneable):

    first_name = models.CharField(
        max_length=30,
        verbose_name=_("first name")
    )

    last_name = models.CharField(
        max_length=30,
        verbose_name=_("last name")
    )

    def clone(self, cls=None, clone=None):
        clone = super(Addressee, self).clone(cls=cls, clone=clone)
        clone.first_name = self.first_name
        clone.last_name = self.last_name
        if settings.BUSINESSES_ALLOWED:
            clone.company_name = self.company_name
        return clone

    def __unicode__(self):
        return u"{0} {1}".format(self.first_name, self.last_name)

    class Meta:
        abstract = True
