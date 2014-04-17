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


from django.conf import settings


from sellmo import modules
from sellmo.api.decorators import chainable
from sellmo.api.configuration import define_setting, define_import
from sellmo.contrib.contrib_checkout.models import OrderMail
from sellmo.contrib.contrib_checkout.mailing import ORDER_MAILS


class CheckoutModule(modules.checkout):
    
    OrderMail = OrderMail
    
    accept_terms_enabled = define_setting(
        'ACCEPT_TERMS_ENABLED',
        default=True)
        
    invoice_writer = define_import(
        'INVOICE_WRITER',
        default='sellmo.contrib.contrib_checkout.reporting.InvoiceWriter')
    
    notification_to_email = define_setting(
        'NOTIFICATION_TO_EMAIL',
        default=settings.DEFAULT_FROM_EMAIL)
        
    order_mails = define_setting(
        'ORDER_MAILS',
        default=ORDER_MAILS)
        
    @chainable()
    def render_order_confirmation(self, chain, format, order, data=None,
                                  **kwargs):
        if chain:
            out = chain.execute(
                format=format, order=order, data=data, **kwargs)
            data = out.get('data', data)
        return data

    @chainable()
    def render_order_notification(self, chain, format, order, data=None,
                                  **kwargs):
        if chain:
            out = chain.execute(
                format=format, order=order, data=data, **kwargs)
            data = out.get('data', data)
        return data

    @chainable()
    def render_shipping_notification(self, chain, format, order, data=None,
                                     **kwargs):
        if chain:
            out = chain.execute(
                format=format, order=order, data=data, **kwargs)
            data = out.get('data', data)
        return data
        
    @chainable()
    def render_invoice(self, chain, order, internal=False, data=None,
                       **kwargs):
        if chain:
            out = chain.execute(
                order=order, internal=internal, data=data, **kwargs)
            data = out.get('data', data)
        return data