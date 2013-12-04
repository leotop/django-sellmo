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

import os.path

#

from django.conf import settings

#

from sellmo.core.reporting.generators import ReportGeneratorBase
from sellmo.contrib.contrib_reporting.piping import pipe, PipeError

#

class PhantomJSReportGenerator(ReportGeneratorBase):

	input_formats = ['html']
	output_formats = ['pdf']
	
	def get_params(self, writer, format):
		params = super(PhantomJSReportGenerator, self).get_params(writer, format)
		# Suggest A4 paper size
		size = writer.negotiate_param('size', 'a4', **params)
	
	def get_data(self, writer, format):
		html = super(PhantomJSReportGenerator, self).get_data(writer, format)
		phantomjs = getattr(settings, 'PHANTOMJS_EXECUTABLE', 'phantomjs')
		script = os.path.join(os.path.dirname(__file__), 'scripts/pdf.js')
		
		try:
			return pipe('{0} {1}'.format(phantomjs, script), input=html)
		except PipeError as error:
			raise
	
	def get_extension(self, format):
		return '.' + format
	
	def get_mimetype(self, format):
		return 'text/' + format