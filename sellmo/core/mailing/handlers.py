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

from sellmo.api.mailing import MailHandler

#

from django.core import mail

#

class MailHandlerBase(MailHandler):

	def send_mail(self, context, connection=None):
		# Open the writer and close it afterwards
		with self.writer.open(context) as writer:
			
			# See if this writer supports both html and text
			if set(['html', 'text']) == set(writer.formats):
				message = mail.EmailMultiAlternatives()
				message.body = writer.get_body('text')
				message.attach_alternative(writer.get_body('html'), 'text/html')
			else:
				message = mail.EmailMessage()
				if 'html' in writer.formats:
					message.content_subtype = 'html'
					message.body = writer.get_body('html')
				elif 'text' in writer.formats:
					message.body = writer.get_body('text')
				else:
					raise Exception("Invalid email formats '{0}'".format(writer.formats))
				
			# Further construct the message
			message.subject = writer.get_subject()
			message.from_email = writer.get_from()
			message.to = writer.get_to()
			message.bcc = writer.get_bcc()
			message.header = writer.get_headers()
			message.attachments = writer.get_attachments()
			
			# If a connection is passed, assign it
			if connection:
				message.connection = connection
			
			# Now actualy send
			message.send()

class DefaultMailHandler(MailHandlerBase):
	def handle_mail(self, context):
		self.send_mail(context)