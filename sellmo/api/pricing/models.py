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

from django.db import models
from django.db.models.query import QuerySet
from django.utils.translation import ugettext_lazy as _

from sellmo import modules
from sellmo.api.decorators import load


@load(action='finalize_pricing_PriceIndexBase')
def finalize_model():
    class PriceIndexBase(modules.pricing.PriceIndexBase):

        class Meta(modules.pricing.PriceIndexBase.Meta):
            abstract = True
            app_label = 'pricing'
    
    modules.pricing.PriceIndexBase = PriceIndexBase


class PriceIndexQuerySet(QuerySet):

    def invalidate(self, **kwargs):
        return self.delete()


class PriceIndexManager(models.Manager):

    def invalidate(self, *args, **kwargs):
        return self.get_query_set().all().invalidate(*args, **kwargs)

    def get_query_set(self):
        return PriceIndexQuerySet(self.model)


class PriceIndexBase(models.Model):
    objects = PriceIndexManager()

    class Meta:
        abstract = True


