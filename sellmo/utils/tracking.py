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


class UntrackableError(Exception):
    pass


def trackable(session_key):

    class TrackableModel(models.Model):

        objects = TrackingManager(session_key)

        def track(self, request):
            if self.pk is None:
                raise UntrackableError("Cannot track non persistent object")
            request.session[session_key] = self.pk

        def untrack(self, request):
            request.session[session_key] = None

        class Meta:
            abstract = True

    return TrackableModel


class TrackingManager(models.Manager):

    def __init__(self, session_key=None, *args, **kwargs):
        self._session_key = session_key
        super(TrackingManager, self).__init__(*args, **kwargs)

    def exists(self, request):
        return request.session.get(self._session_key, False) != False

    def existing(self, request):
        try:
            obj = self.get(pk=request.session.get(self._session_key))
        except self.model.DoesNotExist:
            obj = self.model()
        return obj

    def from_request(self, request):
        if self.exists(request):
            return self.existing(request)
        else:
            return self.model()
