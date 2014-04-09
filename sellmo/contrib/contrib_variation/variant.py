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
from sellmo.contrib.contrib_variation.utils import is_unique_slug

from django.db import models
from django.db.models.signals import m2m_changed
from django.core.exceptions import ValidationError
from django.utils.translation import ugettext_lazy as _
from django.utils.encoding import smart_text
from django.utils.text import capfirst


class ProductUnassignedException(Exception):
    pass


class DuplicateSlugException(Exception):
    pass


def get_differs_field_name(name):
    return '%s_differs' % name


class VariantMixin(object):

    non_variable_fields = ['content_type', 'slug', 'product']
    non_variable_field_types = [models.BooleanField]
    _is_variant = True

    @classmethod
    def setup(cls):
        for field in cls.get_variable_fields():
            descriptor = field.model.__dict__.get(field.name, None)
            setattr(cls, field.name, VariantFieldDescriptor(
                field, descriptor=descriptor))
            cls.add_to_class(
                get_differs_field_name(field.name),
                models.BooleanField(
                    editable=False, auto_created=True, default=False))
        
        for field, reverse in cls.get_m2m_fields():
            modules.variation.mirror_m2m_field(field, reverse)

    @classmethod
    def get_variable_fields(cls):
        fields = cls._meta.fields
        for field in fields:
            if (not field.auto_created
                    and not field.name in cls.non_variable_fields
                    and not field.__class__ in cls.non_variable_field_types
                    and not field in modules.variation.Variant._meta.fields):
                yield field

    @classmethod
    def get_m2m_fields(cls):
        fields = [(field, False) for field in cls._meta.many_to_many]
        fields += [
            (m2m.field, True)
            for m2m, model in 
            cls._meta.get_all_related_m2m_objects_with_model()]
        
        for field, reverse in fields:
            if not reverse or not field.rel.related_name.endswith('+'):
                yield field, reverse

    def get_product(self):
        if hasattr(self, 'product_id') and self.product_id != None:
            return self.product
        return None

    def validate_unique(self, exclude=None):
        super(self.__class__.__base__, self).validate_unique(exclude)
        if 'slug' not in exclude:
            if not is_unique_slug(self.slug, ignore=self):
                model_name = modules.product.Product._meta.verbose_name
                model_name = capfirst(model_name)
                message = _(
                    "{model_name}s with this "
                    "{field_label}s already exists.").format(
                        model_name=model_name,
                        field_label='slug')
                raise ValidationError({'slug': [message]})

    def save(self, *args, **kwargs):
        product = self.get_product()
        if not product:
            raise ProductUnassignedException()

        # See if object is newly created
        try:
            exists = not self.pk is None
        except Exception:
            exists = False

        def assign_field(field, val, product_val):
            differs = getattr(self, get_differs_field_name(field.name))

            if not val:
                # Empty field will always copy it's parent field.
                val = product_val
                differs = False
            elif not exists and val != product_val:
                # Descriptor won't work for newly created variants.
                # Set differs to True manually
                differs = True
            elif not differs and val != product_val:
                # Parent has changed, copy field value.
                val = product_val
            elif differs and val == product_val:
                # We don't differ anymore
                differs = False

            setattr(self, field.name, val)
            setattr(self, get_differs_field_name(field.name), differs)

        # Copy fields
        for field in self.__class__.get_variable_fields():
            val = getattr(self, field.name)
            product_val = getattr(product, field.name)
            assign_field(field, val, product_val)

        super(VariantMixin, self).save(*args, **kwargs)

    class Meta:
        app_label = 'product'
        verbose_name = _("variant")
        verbose_name_plural = _("variants")


class VariantFieldDescriptor(object):

    def __init__(self, field, descriptor=None):
        self.field = field
        self.descriptor = descriptor

    def __get__(self, obj, objtype):
        if not self.descriptor:
            return obj.__dict__.get(self.field.name, None)
        else:
            return self.descriptor.__get__(obj, objtype)

    def __set__(self, obj, val):

        # See if object is newly created
        try:
            exists = not obj.pk is None
        except Exception:
            exists = False

        if exists:
            # See if we differ and keep track
            differs = getattr(
                obj, get_differs_field_name(self.field.name), False)
            if not differs:
                try:
                    # In case we are initializing, an exception could occur while
                    # getting this field's value
                    old_val = getattr(obj, self.field.name)
                except Exception:
                    pass
                else:
                    differs = not old_val is None and old_val != val
                    setattr(
                        obj, get_differs_field_name(self.field.name), differs)

        # Now set
        if not self.descriptor:
            obj.__dict__[self.field.name] = val
        else:
            self.descriptor.__set__(obj, val)
