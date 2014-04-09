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


from django.utils.module_loading import import_by_path

from sellmo.magic import singleton
from sellmo.config import settings


@singleton
class Reporter(object):

    input_format_mapping = None
    output_format_mapping = None
    writers = {}

    def __init__(self):
        pass

    def map_generators(self):

        if self.input_format_mapping is not None:
            return

        self.input_format_mapping = {}
        self.output_format_mapping = {}

        # Map generators
        for generator in settings.REPORT_GENERATORS:
            generator = import_by_path(generator)
            if not generator.input_formats or not generator.output_formats:
                raise Exception("Generator needs input and output formats")

            # Map to input formats
            for format in generator.input_formats:
                if format not in self.input_format_mapping:
                    self.input_format_mapping[format] = set()
                self.input_format_mapping[format].add(generator)
            # Map to output formats
            for format in generator.output_formats:
                if format not in self.output_format_mapping:
                    self.output_format_mapping[format] = set()
                self.output_format_mapping[format].add(generator)

    def get_report(self, report_type, format=None, context=None):

        self.map_generators()

        # Assign defaults
        if context is None:
            context = {}
        if format is None:
            format = settings.REPORT_FORMAT

        # Find all acceptable formats
        input_formats = set([format])
        if format in self.output_format_mapping:
            for generator in self.output_format_mapping[format]:
                input_formats = set(generator.input_formats) | input_formats

        # Find writer
        if not report_type in self.writers:
            raise Exception(
                "No writer for report type '{0}'".format(report_type))
        for input_format in input_formats:
            if input_format in self.writers[report_type]:
                writer = self.writers[report_type][input_format]
                break
        else:
            raise Exception("Format '{0}' is not supported".format(format))

        # Find the generator with both correct input and output
        generators = self.output_format_mapping[
            format] & self.input_format_mapping[writer.format]
        generator = list(generators)[0]

        # Create a new generator and generate report
        generator = generator(writer)
        return generator.generate_report(format, context)

    def register(self, report_type, writer):
        if isinstance(writer, (str, unicode)):
            writer = import_by_path(writer)

        if not writer.format:
            raise Exception("Writer needs format")

        # Map writer to report_type and writer format
        if report_type not in self.writers:
            self.writers[report_type] = {}
        self.writers[report_type][writer.format] = writer


reporter = Reporter()
