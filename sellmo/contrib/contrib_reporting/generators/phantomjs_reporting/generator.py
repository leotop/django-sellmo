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
import codecs

#

from django.conf import settings as django_settings

#

from sellmo.core.reporting.generators import ReportGeneratorBase
from sellmo.contrib.contrib_reporting.config import settings
from sellmo.contrib.contrib_reporting.piping import pipe, PipeError

#

class PhantomJSReportGenerator(ReportGeneratorBase):

    input_formats = ['html']
    output_formats = ['pdf', 'png']
    
    def get_params(self, writer, format):
        params = super(PhantomJSReportGenerator, self).get_params(writer, format)
        suggest_params = settings.REPORTING_PARAMS.get(format, {})
        
        for param, suggest in suggest_params.iteritems():
            value = writer.negotiate_param(param, suggest, **params)
            params[param] = value if not value is False else suggest
        
        return params
    
    def get_data(self, writer, format):
        html = super(PhantomJSReportGenerator, self).get_data(writer, format)
        params = self.get_params(writer, format)
        
        # Create command
        phantomjs = getattr(django_settings, 'PHANTOMJS_EXECUTABLE', 'phantomjs')
        script = os.path.join(os.path.dirname(__file__), 'scripts/render.js')
        arguments = ['format={0}'.format(format)]
        
        # Create command arguments
        for param, value in params.iteritems():
            arguments += ['{0}={1}'.format(param, params[param])]
        arguments = ' '.join(arguments)
        
        # Encode as UTF8
        html = codecs.encode(html, 'utf8')
        
        try:
            return pipe('{0} {1} {2}'.format(phantomjs, script, arguments), input=html)
        except PipeError:
            raise
    
    def get_extension(self, format):
        return '.' + format
    
    def get_mimetype(self, format):
        if format == 'pdf':
            return 'application/pdf'
        elif format == 'png':
            return 'image/png';