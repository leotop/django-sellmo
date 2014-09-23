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


from decimal import Decimal

from sellmo import modules
from sellmo.api.decorators import load
from sellmo.api.pricing import Price

from django.db import models
from django.utils.translation import ugettext_lazy as _


@load(action='load_discount_subtypes')
@load(after='finalize_discount_Discount')
def load_subtypes():

    class PercentDiscount(modules.discount.Discount):

        rate = modules.pricing.construct_decimal_field(
            default=Decimal('0.0'),
            verbose_name=_("rate"),
        )

        def apply(self, price):
            amount = price.amount * self.rate
            discount = Price(
                amount, currency=price.currency, type='discount', 
                context={'discount': self})
            return price - discount

        class Meta(modules.discount.Discount.Meta):
            app_label = 'discount'
            verbose_name = _("percent discount")
            verbose_name_plural = _("percent discounts")

    modules.discount.register_subtype(PercentDiscount)
