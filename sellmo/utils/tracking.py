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


import types

from django.db import models
from django.db.models.query import QuerySet


class UntrackableError(Exception):
    pass


def trackable(session_key):
    manager = TrackingManager()
    manager._session_key = session_key
    
    class TrackableModel(models.Model):

        objects = manager

        def track(self, request):
            if self.pk is None:
                raise UntrackableError("Cannot track non persistent object")
            request.session[session_key] = self.pk

        def untrack(self, request):
            request.session[session_key] = None

        class Meta:
            abstract = True

    return TrackableModel
    
    
class TrackingBase(object):
    
    _session_key = None
    
    def is_tracked(self, request):
        return self._get_session_key() in request.session
    
    def _get_session_key(self):
        if self._session_key is None:
            raise Exception("Session related operations cannot be performed")
        return self._session_key
    
class TrackingQuerySet(TrackingBase, QuerySet):
    
    def try_get_tracked(self, request):
        if self.is_tracked(request):
            try:
                return self.get(pk=request.session.get(self._get_session_key()))
            except self.model.DoesNotExist:
                pass
        return self.model()
            
    def _clone(self, *args, **kwargs):
        clone = super(TrackingQuerySet, self)._clone(*args, **kwargs)
        clone._session_key = self._session_key
        return clone

class TrackingManager(TrackingBase, models.Manager):
    
    def try_get_tracked(self, *args, **kwargs):
        return self.get_queryset().try_get_tracked(*args, **kwargs)
    
    def get_queryset(self):
        qs = TrackingQuerySet(self.model, using=self._db)
        qs._session_key = self._session_key
        return qs
