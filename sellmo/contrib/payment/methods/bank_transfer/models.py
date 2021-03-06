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
from sellmo.contrib.payment \
     .methods.bank_transfer import BankTransferPaymentMethod

from django.db import models
from django.utils.translation import ugettext_lazy as _


@load(action='finalize_bank_transfer_Payment')
@load(after='finalize_checkout_Payment')
def finalize_model():

    class BankTransferPayment(
            modules.checkout.Payment,
            modules.bank_transfer.BankTransferPayment):

        instant = False

        def get_method(self):
            return BankTransferPaymentMethod()

        def __unicode__(self):
            return unicode(self.get_method())

        class Meta(modules.bank_transfer.BankTransferPayment.Meta):
            app_label = 'checkout'

    modules.bank_transfer.BankTransferPayment = BankTransferPayment


class BankTransferPayment(models.Model):

    class Meta:
        abstract = True
        verbose_name = _("bank transfer payment")
        verbose_name_plural = _("bank transfers payments")
