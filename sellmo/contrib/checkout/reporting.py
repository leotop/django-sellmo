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
from sellmo.api.reporting import ReportWriter

from django.utils.translation import ugettext_lazy as _


class OrderConfirmationWriter(ReportWriter):

    format = 'html'

    def __init__(self, output_format, order, internal=False):
        self.output_format = output_format
        self.order = order
        self.internal = internal

    def get_name(self):
        return "confirmation_{0}".format(self.order.number)

    def negotiate_param(self, key, value, **params):
        return super(OrderConfirmationWriter, self).negotiate_param(
            key, value, **params)

    def get_data(self, **params):
        return modules.checkout.render_order_confirmation_report(
            order=self.order, internal=self.internal)
            
            
class InvoiceWriter(ReportWriter):

    format = 'html'

    def __init__(self, output_format, order, internal=False):
        self.output_format = output_format
        self.order = order
        self.internal = internal

    def get_name(self):
        return "invoice_{0}".format(self.order.number)

    def negotiate_param(self, key, value, **params):
        return super(InvoiceWriter, self).negotiate_param(key, value, **params)

    def get_data(self, **params):
        return modules.checkout.render_invoice_report(
            order=self.order, internal=self.internal)
