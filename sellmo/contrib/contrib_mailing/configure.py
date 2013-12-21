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

import uuid
import logging
import datetime

#

from sellmo.signals.mailing import mail_init, mail_send, mail_failed

#

def on_mail_init(sender, message_type, message_reference, **kwargs):
	logger.info("Mail message {0} initialized.".format(message_reference))
	status = MailStatus.objects.get_or_create(message_reference=message_reference)

def on_mail_send(sender, message_type, message_reference, **kwargs):
	logger.info("Mail message {0} send successfully.".format(message_reference))
	try:
		status = MailStatus.objects.get(message_reference=message_reference)
	except MailStatus.DoesNotExist:
		pass
	else:
		status.delivered = datetime.datetime.now()
		status.save()

def on_mail_failed(sender, message_type, message_reference, reason='', **kwargs):
	logger.warning("Mail message {0} failed to send. Reason: {1}".format(message_reference, reason))
	try:
		status = MailStatus.objects.get(message_reference=message_reference)
	except MailStatus.DoesNotExist:
		pass
	else:
		status.failed = datetime.datetime.now()
		status.failure_message = reason
		status.save()

mail_init.connect(on_mail_init)
mail_send.connect(on_mail_send)
mail_failed.connect(on_mail_send)