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
from sellmo.api.pricing import Price
from django.utils.translation import ugettext_lazy as _


__all__ = [
    'ShippingMethod',
    'PaymentMethod',
]


class MethodBase(object):

    def get_name(self):
        raise NotImplementedError()
    name = property(get_name)

    def get_identifier(self):
        raise NotImplementedError()
    identifier = property(get_identifier)

    def get_costs(self, order, **kwargs):
        raise NotImplementedError()

    def is_available(self, order, **kwargs):
        return True

    def process(self, request, order, next_step):
        return next_step

    def __unicode__(self):
        return unicode(self.name)


class ShippingMethod(MethodBase):

    def new_shipment(self, order):
        raise NotImplementedError()

    def ship(self, order):
        if not self.is_available(order):
            raise Exception(_("Invalid shipping method for this order"))
        shipment = self.new_shipment(order)
        shipment.costs = self.get_costs(order=order)
        shipment.save()
        if order.shipment:
            order.shipment.delete()
        order.shipment = shipment
        order.save()


class PaymentMethod(MethodBase):

    def new_payment(self, order):
        raise NotImplementedError()

    def pay(self, order):
        if not self.is_available(order):
            raise Exception(_("Invalid payment method for this order"))
        payment = self.new_payment(order)
        payment.costs = self.get_costs(order=order)
        payment.save()
        if order.payment:
            order.payment.delete()
        order.payment = payment
        order.save()
