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
from sellmo.api.pricing import Price
from sellmo.contrib.shipping \
     .methods.flat_shipping import FlatShippingMethod as _FlatShippingMethod

from django.db import models
from django.utils.translation import ugettext_lazy as _


@load(action='load_shipping_subtypes')
@load(after='finalize_shipping_ShippingMethod')
def load_subtypes():

    class FlatShippingMethod(modules.shipping.ShippingMethod):

        costs = modules.pricing.construct_pricing_field(
            verbose_name=_("shipping rate"),
        )

        def get_method(self, carrier=None):
            name = self.name
            identifier = self.identifier
            if carrier:
                name = _(u"{0} by {1}").format(name, carrier.name)
                identifier = '{0}_{1}'.format(identifier, carrier.identifier)
            return _FlatShippingMethod(
                identifier, name, method=self, carrier=carrier)

        class Meta(modules.shipping.ShippingMethod.Meta):
            app_label = 'shipping'
            verbose_name = _("flat shipping method")
            verbose_name_plural = _("flat shipping methods")

    modules.shipping.register_subtype(FlatShippingMethod)
