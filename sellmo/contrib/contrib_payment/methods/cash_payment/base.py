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

from sellmo import modules
from sellmo.api.pricing import Price
from sellmo.api.checkout import PaymentMethod

#

from django.utils.translation import ugettext_lazy as _

#

class CashPaymentMethod(PaymentMethod):

    identifier = 'cash'
    name = _("cash payment")
    
    def process(self, order, request, next_step):
        return next_step
        
    def is_available(self, order):
        if order.shipment:
            identifier = order.shipment.get_method().identifier.split('_')[0]
            return modules.shipping.ShippingMethod.objects.filter(
                allow_cash_payment=True,
                identifier=identifier
            ).count() == 1
        return True

    def new_payment(self, order):
        return modules.cash_payment.CashPayment()

    def get_costs(self, order, currency=None, **kwargs):
        return modules.pricing.get_price(price=Price(0), payment_method=self)

    def __unicode__(self):
        settings = modules.settings.get_settings()
        if settings.cash_payment_name:
            return settings.cash_payment_name
        return super(CashPaymentMethod, self).__unicode__()