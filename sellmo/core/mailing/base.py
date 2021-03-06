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


import uuid

from django.utils.module_loading import import_by_path

from sellmo.api.configuration import define_import
from sellmo.signals.mailing import mail_init


class Mailer(object):

    handler = define_import(
        'MAIL_HANDLER',
        default='sellmo.core.mailing.handlers.DefaultMailHandler')
    
    writers = {}

    def send_mail(self, message_type, context=None):

        # Create unique message reference for internal usages
        message_reference = uuid.uuid1().hex

        # Notify
        mail_init.send(
            sender=self,
            message_type=message_type,
            message_reference=message_reference,
            context=context
        )

        if context is None:
            context = {}

        # Find writer
        if not message_type in self.writers:
            raise Exception(
                "No writer for message type '{0}'".format(message_type))
        writer = self.writers[message_type]

        # Create a new handler with the given writer
        handler = self.handler(writer)

        # Handle the email
        handler.handle_mail(message_type, message_reference, context)
        return message_reference

    def register(self, message_type, writer):
        if isinstance(writer, (str, unicode)):
            writer = import_by_path(writer)
        self.writers[message_type] = writer

mailer = Mailer()
