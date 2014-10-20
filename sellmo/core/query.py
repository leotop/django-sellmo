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


from django.db.models.query import QuerySet


class PKIterator(object):

    """
    Queries a set of pks against the given model. Seperate 
    queries are used if the length of 'pks' exceeds 'step'.
    This in order to limit the length of the sql IN clause.
    Order of pks is kept. If pk is not found, it will be 
    ignored.
    """

    _result_cache = None
    _queryset = None

    def __init__(self, model_or_queryset, pks, step=250):
        if not isinstance(model_or_queryset, QuerySet):
            # Must be a Model then
            model_or_queryset = model_or_queryset.objects.all()
        self._queryset = model_or_queryset
        self._pks = list(pks)
        self._step = step

    def __iter__(self):
        if self._result_cache is None:
            self._result_cache = {}
            for i in xrange(0, len(self._pks), self._step):
                sliced = self._pks[i:i+self._step]
                for obj in self._queryset.filter(pk__in=sliced):
                    self._result_cache[obj.pk] = obj
        for pk in self._pks:
            obj = self._result_cache.get(pk, None)
            if obj is not None:
                yield obj

    def __len__(self):
        if self._result_cache is None:
            list(self.__iter__())
        return len(self._result_cache)