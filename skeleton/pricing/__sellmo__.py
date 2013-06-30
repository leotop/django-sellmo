from sellmo import modules
from sellmo.api.pricing import Currency

#

from django.db import models
from django.utils.translation import ugettext_lazy as _

#

namespace = modules.pricing.namespace
modules.pricing.currency = Currency('usd', _(u"U.S Dolalrs"), _(u"$ {amount:.2f},-"))