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
from sellmo.api.decorators import load

from django.db import models
from django.utils.translation import ugettext_lazy as _


@load(before='finalize_customer_Addressee')
def load_model():

    class Addressee(modules.customer.Addressee):

        if modules.customer.name_prefix_enabled:
            prefix = models.CharField(
                max_length=20,
                verbose_name=_("prefix"),
                blank=not modules.customer.name_prefix_required,
                choices=modules.customer.name_prefix_choices,
                default=modules.customer.name_prefix_choices[0][0]
            )

        if modules.customer.name_suffix_enabled:
            suffix = models.CharField(
                max_length=10,
                blank=True,
                verbose_name=_("suffx"),
            )

        def clone(self, cls=None, clone=None):
            clone = super(Addressee, self).clone(cls=cls, clone=clone)
            clone.suffix = self.suffix
            if modules.customer.name_prefix_enabled:
                clone.prefix = self.prefix
            return clone

        class Meta(modules.customer.Addressee.Meta):
            abstract = True

    modules.customer.Addressee = Addressee


@load(before='finalize_customer_Contactable')
def load_model():
    class Contactable(modules.customer.Contactable):

        if modules.customer.phone_number_enabled:
            phone_number = models.CharField(
                max_length=20,
                blank=not modules.customer.phone_number_required,
                verbose_name=_("phone number"),
            )

        def clone(self, cls=None, clone=None):
            clone = super(Contactable, self).clone(cls=cls, clone=clone)
            if modules.customer.phone_number_enabled:
                clone.phone_number = self.phone_number
            return clone

        class Meta(modules.customer.Contactable.Meta):
            abstract = True

    modules.customer.Contactable = Contactable
