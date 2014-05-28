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


from django.http import HttpRequest
from django.contrib import messages
from django.contrib.messages import constants


class FlashMessages(object):
    
    def __init__(self):
        self._messages = []
        
    def transmit(self):
        for message in self:
            messages.add_message(**message)
        
    def clear(self):
        self._messages = []
        
    def add_message(self, request, level, message, extra_tags='',
                    fail_silently=False):
        """
        Attempts to add a message to the request using the 'messages' app.
        """
        if not isinstance(request, HttpRequest):
            raise TypeError("add_message() argument must be an HttpRequest "
                            "object, not '%s'." % request.__class__.__name__)
        self._messages.append({
            'request': request,
            'level': level,
            'message': message,
            'extra_tags': extra_tags,
            'fail_silently': fail_silently
        })
        
    def debug(self, request, message, extra_tags='', fail_silently=False):
        """
        Adds a message with the ``DEBUG`` level.
        """
        self.add_message(request, constants.DEBUG, message,
                    extra_tags=extra_tags, fail_silently=fail_silently)
    
    
    def info(self, request, message, extra_tags='', fail_silently=False):
        """
        Adds a message with the ``INFO`` level.
        """
        self.add_message(request, constants.INFO, message,
                    extra_tags=extra_tags, fail_silently=fail_silently)
    
    
    def success(self, request, message, extra_tags='', fail_silently=False):
        """
        Adds a message with the ``SUCCESS`` level.
        """
        self.add_message(request, constants.SUCCESS, message,
                    extra_tags=extra_tags, fail_silently=fail_silently)
    
    
    def warning(self, request, message, extra_tags='', fail_silently=False):
        """
        Adds a message with the ``WARNING`` level.
        """
        self.add_message(request, constants.WARNING, message,
                    extra_tags=extra_tags, fail_silently=fail_silently)
    
    
    def error(self, request, message, extra_tags='', fail_silently=False):
        """
        Adds a message with the ``ERROR`` level.
        """
        self.add_message(request, constants.ERROR, message,
                    extra_tags=extra_tags, fail_silently=fail_silently)
                    
    def __iter__(self):
        for message in self._messages:
            yield message
            
    def __len__(self):
        return len(self._messages)