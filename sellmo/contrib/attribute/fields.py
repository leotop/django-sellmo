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


from sellmo import modules
from sellmo.contrib.attribute.types import AttributeType

import re

from django.db import models
from django.core.exceptions import ValidationError
from django.utils.translation import ugettext_lazy as _


class AttributeKeyField(models.SlugField):

    def validate(self, value, instance):
        super(AttributeKeyField, self).validate(value, instance)
        key_regex = r'[a-z][a-z0-9_]*'
        if not re.match(key_regex, value):
            raise ValidationError(_("Must be all lower case, "
                                    "start with a letter, and contain "
                                    "only letters, numbers, or underscores."))
        if value in modules.product.reserved_url_params:
            raise ValidationError(_("Conflicts with url parameter"))

    @staticmethod
    def create_key_from_name(name):

        name = name.strip().lower()

        # Change spaces to underscores
        name = '_'.join(name.split())

        # Remove non alphanumeric characters
        return re.sub('[^\w]', '', name)


class AttributeTypeField(models.CharField):

    def validate(self, value, instance):
        super(AttributeTypeField, self).validate(value, instance)
        old = None

        if instance.pk:
            old = modules.attribute.Attribute.objects.get(pk=instance.pk)

        if not old or value == old.type:
            return

        if instance.values.count() > 0:
            raise ValidationError(
                _("Cannot change attribute type "
                  "of an attribute that is already in use."))