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

from django.db import models
from django.utils.translation import ugettext_lazy as _

#

from sellmo import modules
from sellmo.api.decorators import load

#

@load(action='finalize_mailing_MailStatus')
def finalize_model():
	class MailStatus(modules.mailing.MailStatus):
		class Meta(modules.mailing.MailStatus.Meta):
			app_label = 'mailing'
			verbose_name = _("mail status")
			verbose_name_plural = _("mail statuses")
	
	modules.mailing.MailStatus = MailStatus

class MailStatus(models.Model):

	message_reference = models.CharField(
		max_length = 32,
		editable = False,
		unique = True,
		db_index = True,
	)

	message_type = models.CharField(
		max_length = 80,
		editable = False,
		db_index = True,
	)

	created = models.DateTimeField(
		auto_now_add = True,
		editable = False,
		verbose_name = _("created at"),
	)

	send = models.DateTimeField(
		null = True,
		editable = False,
		verbose_name = _("send at"),
	)
	
	send_to = models.TextField(
		editable = False,
		verbose_name = _("send to"),
	)
	
	delivered = models.BooleanField(
		default = False,
		editable = False,
	)

	failure_message = models.TextField(
		editable = False,
		verbose_name = _("failure message"),
	)
	
	def __unicode__(self):
		return u"{0} - {1}".format(self.message_type, self.message_reference)

	class Meta:
		abstract = True
