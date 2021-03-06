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


@load(before='finalize_customer_Address')
def load_model():
    class Address(modules.customer.Address):

        street_name = models.CharField(
            max_length=80,
            verbose_name=_("street name")
        )

        house_number = models.CharField(
            max_length=10,
            verbose_name=_("house number")
        )

        postal_code = models.CharField(
            max_length=15,
            verbose_name=_("postal code")
        )

        city = models.CharField(
            max_length=50,
            verbose_name=_("city")
        )

        def clone(self, cls=None, clone=None):
            clone = super(Address, self).clone(cls=cls, clone=clone)
            clone.street_name = self.street_name
            clone.house_number = self.house_number
            clone.postal_code = self.postal_code
            clone.city = self.city
            return clone

        class Meta(modules.customer.Address.Meta):
            abstract = True

    modules.customer.Address = Address
