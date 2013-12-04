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

from sellmo.config import settings

#

class MailHandler(object):

	def __init__(self, writer):
		self.writer = writer

	def handle_mail(self, context):
		raise NotImplementedError()

class MailWriter(object):
	
	# Can be either text, html or both
	formats = ['text']
	
	@classmethod
	def open(cls, context=None):
		if context is None:
			context = {}
		return cls(**context)
	
	def __init__(self, **context):
		self.context = context
	
	def __enter__(self):
		self.setup()
		return self
	
	def __exit__(self, type, value, traceback):
		self.teardown()
	
	def setup(self):
		pass
		
	def teardown(self):
		pass
	
	def get_to(self):
		raise NotImplementedError()
		
	def get_subject(self):
		raise NotImplementedError()
	
	def get_body(self, format):
		raise NotImplementedError()
		
	def get_bcc(self):
		return []
		
	def get_from(self):
		return settings.MAIL_FROM
		
	def get_attachments(self):
		return []
		
	def get_headers(self):
		return {}
		
