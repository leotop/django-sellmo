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


from sellmo.api.configuration import get_setting
from sellmo.core.mailing.handlers import MailHandlerBase
from sellmo.core.mailing import mailer

from celery import shared_task, Task


send_mail_retry_enabled = get_setting(
    'SEND_MAIL_RETRY_ENABLED',
    default=True)
                            
send_mail_retry_delay = get_setting(
    'SEND_MAIL_RETRY_DELAY',
    default=5 * 60)
                                    
send_mail_retry_limit = get_setting(
    'SEND_MAIL_RETRY_LIMIT',
    default=3)                                


@shared_task
def send_mail(message_type, message_reference, context):
    writer = mailer.writers[message_type]
    handler = MailHandlerBase(writer)
    try:
        handler.send_mail(message_type, message_reference, context)
    except Exception as exc:
        if send_mail_retry_enabled:
            raise send_mail.retry(
                countdown=send_mail_retry_delay,
                max_retries=send_mail_retry_limit,
                exc=exc
            )
        raise
