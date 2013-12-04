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

from sellmo.api.reporting import ReportGenerator, Report

#

class ReportGeneratorBase(ReportGenerator):
	def generate_report(self, format, context=None):
		with self.writer.open(format, context) as writer:
			return Report(
				self.get_filename(writer, format),
				self.get_data(writer, format),
				self.get_mimetype(format)
			)
			
	def get_params(self, writer, format):
		return {}
			
	def get_data(self, writer, format):
		params = self.get_params(writer, format)
		if params is None:
			params = {}
		return writer.get_data(**params)
		
	def get_filename(self, writer, format):
		ext = self.get_extension(format)
		if not ext or not ext.startswith('.'):
			raise Exception("Invalid extension")
		return writer.get_name() + ext
			
	def get_extension(self, format):
		raise NotImplementedError()
		
	def get_mimetype(self, format):
		raise NotImplementedError()
	