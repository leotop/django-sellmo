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

from sellmo import modules
from sellmo.api.decorators import load

#

from django.db import models
from django.utils.translation import ugettext_lazy as _

#

@load(before='finalize_customer_Addressee')
def load_model():
	
	prefix_choices = (
		('sir', _("sir")),
		('madame', _("madam")),
	) if not getattr(modules.customer, 'prefixes', False) else getattr(modules.customer, 'prefixes') 
	
	class Addressee(modules.customer.Addressee):
		
		if getattr(modules.customer, 'prefix_enabled', False):
			prefix = models.CharField(
				max_length = 20,
				verbose_name = _("prefix"),
				blank = not getattr(modules.customer, 'prefix_required', True),
				choices = prefix_choices,
				default = prefix_choices[0][0]
			)
		
		suffix = models.CharField(
			max_length = 10,
			blank = True,
			verbose_name = _("suffx"),
		)
		
		def clone(self, cls=None):
			clone = super(Addressee, self).clone(cls=cls)
			clone.suffix = self.suffix
			if getattr(modules.customer, 'prefix_enabled', False):
				clone.prefix = self.prefix
			return clone

		class Meta:
			abstract = True

	modules.customer.Addressee = Addressee