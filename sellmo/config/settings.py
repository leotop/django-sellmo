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

from django.conf import settings

#

from sellmo.config import defaults

#

debug = getattr(settings, 'DEBUG', False)

#

CUSTOMER_REQUIRED = getattr(settings, 'SELLMO_CUSTOMER_REQUIRED', defaults.CUSTOMER_REQUIRED)
REQUIRED_ADDRESS_TYPES = getattr(settings, 'SELLMO_REQUIRED_ADDRESS_TYPES', defaults.REQUIRED_ADDRESS_TYPES)
ORDER_STATUSES = getattr(settings, 'SELLMO_ORDER_STATUSES', defaults.ORDER_STATUSES)

#

REDIRECTION_SESSION_PREFIX = getattr(settings, 'SELLMO_REDIRECTION_SESSION_PREFIX', defaults.REDIRECTION_SESSION_PREFIX)
REDIRECTION_DEBUG = getattr(settings, 'SELLMO_REDIRECTION_DEBUG', defaults.REDIRECTION_DEBUG and debug)

#

CACHING_ENABLED = getattr(settings, 'SELLMO_CACHING_ENABLED', defaults.CACHING_ENABLED)
CACHING_PREFIX = getattr(settings, 'SELLMO_CACHING_PREFIX', defaults.CACHING_PREFIX)

#

CELERY_ENABLED = getattr(settings, 'SELLMO_CELERY_ENABLED', defaults.CELERY_ENABLED)

#

MAIL_HANDLER = getattr(settings, 'SELLMO_MAIL_HANDLER', defaults.MAIL_HANDLER)
MAIL_FROM = getattr(settings, 'SELLMO_MAIL_FROM', defaults.MAIL_FROM)

#

REPORT_GENERATORS = getattr(settings, 'SELLMO_REPORT_GENERATORS', defaults.REPORT_GENERATORS)
REPORT_FORMAT = getattr(settings, 'SELLMO_REPORT_FORMAT', defaults.REPORT_FORMAT)