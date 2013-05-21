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

import types

#

from django.db import models

#

def make_trackable(obj, session_key):
    def track(self, request):
        if self.pk is None:
            raise Exception("Cannot track not persistent object")
        request.session[session_key] = self.pk
    obj.track = track.__get__(obj, obj.__class__)
    return obj

#

class TrackingManager(models.Manager):
    
    def __init__(self, session_key, *args, **kwargs):
        self._session_key = session_key
        super(TrackingManager, self).__init__(*args, **kwargs)
    
    def _exists(self, request):
        return request.session.get(self._session_key, False) != False
            
    def _new(self, request):
        obj = self.model()
        return make_trackable(obj, self._session_key)

    def _existing(self, request):
        try:
            obj = self.get(pk=request.session.get(self._session_key))
            obj.is_tracked = True
        except self.model.DoesNotExist:
            obj = self._new(request)
        return make_trackable(obj, self._session_key)
    
    def from_request(self, request):
        if self._exists(request):
            return self._existing(request)
        else:
            return self._new(request)