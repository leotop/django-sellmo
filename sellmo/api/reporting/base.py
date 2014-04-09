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


from sellmo.config import settings


class Report(object):

    def __init__(self, filename, data, mimetype):
        self.filename = filename
        self.data = data
        self.mimetype = mimetype


class ReportGenerator(object):

    output_formats = []
    input_formats = []

    def __init__(self, writer):
        self.writer = writer

    def generate_report(self, format, context=None):
        """
        Returns a Report instance
        """
        raise NotImplementedError()


class ReportWriter(object):

    """
    The format this writer will output
    """
    format = None
    params = {}

    @classmethod
    def open(cls, output_format, context=None):
        if context is None:
            context = {}
        return cls(output_format, **context)

    def __init__(self, output_format,  **context):
        self.output_format = output_format
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

    def get_name(self):
        raise NotImplementedError()

    def get_data(self, **params):
        raise NotImplementedError()

    def negotiate_param(self, key, value, **params):
        """
        False if we don't understand. The same value if we accept or a
        different value if we want to change.
        """
        if key in self.params:
            return self.params[key]
        return False
