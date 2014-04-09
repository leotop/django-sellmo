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


from django.db import transaction, models
from django.db.models import OneToOneField, ForeignKey
from django.contrib.admin import helpers, ModelAdmin
from django.contrib.admin.options import InlineModelAdmin
from django.contrib.admin.util import flatten_fieldsets
from django.forms import ModelForm
from django.forms.formsets import all_valid
from django.forms.models import BaseModelFormSet, modelformset_factory
from django.utils.encoding import force_unicode
from django.utils.functional import curry
from django.utils.safestring import mark_safe
from django.utils.translation import ugettext as _
from django.core.exceptions import PermissionDenied


class ReverseInlineFormSet(BaseModelFormSet):
    model = None
    parent_fk_name = None

    def __init__(self, data=None, files=None, instance=None, prefix=None,
                 queryset=None, save_as_new=False):
        try:
            obj = getattr(instance, self.parent_fk_name)
        except self.model.DoesNotExist:
            obj = None

        if obj:
            queryset = self.model.objects.filter(pk=obj.id)
        else:
            queryset = self.model.objects.none()

        if queryset.count() == 0:
            self.extra = 1
        super(ReverseInlineFormSet, self).__init__(
            data, files, prefix=prefix, queryset=queryset)


def reverse_inlineformset_factory(parent_model, model, parent_fk_name,
                                  form=ModelForm, fields=None, exclude=None,
                                  formfield_callback=lambda f: f.formfield()):
    kwargs = {
        'form': form,
        'formfield_callback': formfield_callback,
        'formset': ReverseInlineFormSet,
        'extra': 0,
        'can_delete': False,
        'can_order': False,
        'fields': fields,
        'exclude': exclude,
        'max_num': 1,
    }

    FormSet = modelformset_factory(model, **kwargs)
    FormSet.parent_fk_name = parent_fk_name
    return FormSet


class ReverseInlineModelAdmin(InlineModelAdmin):

    def __init__(self, parent_model, parent_fk_name, model, admin_site,
                 inline_type):
        self.template = 'admin/edit_inline/%s.html' % inline_type
        self.parent_fk_name = parent_fk_name
        self.model = model
        field_descriptor = getattr(parent_model, self.parent_fk_name)
        field = field_descriptor.field

        self.verbose_name_plural = field.verbose_name.title()
        self.verbose_name = field.help_text
        if not self.verbose_name:
            self.verbose_name = self.verbose_name_plural
        super(ReverseInlineModelAdmin, self).__init__(parent_model, admin_site)

    def get_formset(self, request, obj=None, **kwargs):
        if self.declared_fieldsets:
            fields = flatten_fieldsets(self.declared_fieldsets)
        else:
            fields = None
        if self.exclude is None:
            exclude = []
        else:
            exclude = list(self.exclude)
        # if exclude is an empty list we use None, since that's the actual
        # default
        exclude = (exclude + kwargs.get("exclude", [])) or None
        defaults = {
            "form": self.form,
            "fields": fields,
            "exclude": exclude,
            "formfield_callback": curry(
                self.formfield_for_dbfield, request=request),
        }
        defaults.update(kwargs)
        return reverse_inlineformset_factory(
            self.parent_model, self.model, self.parent_fk_name, **defaults)


class ReverseModelAdmin(ModelAdmin):

    def __init__(self, *args, **kwargs):
        super(ReverseModelAdmin, self).__init__(*args, **kwargs)
        if self.exclude is None:
            self.exclude = []

    def get_inline_instances(self, request, obj=None):
        inline_instances = super(
            ReverseModelAdmin, self).get_inline_instances(request, obj)
        for field_name in self.inline_reverse:
            kwargs = {}
            if isinstance(field_name, tuple):
                if isinstance(field_name[1], dict):
                    kwargs = field_name[1]
                elif isinstance(field_name[1], ModelForm):
                    kwargs['form'] = field_name[1]
                field_name = field_name[0]

            field = self.model._meta.get_field(field_name)
            if isinstance(field, (OneToOneField, ForeignKey)):
                name = field.name
                parent = field.related.parent_model
                inline = ReverseInlineModelAdmin(
                    self.model, name, parent, 
                    self.admin_site, self.inline_type)
                if kwargs:
                    inline.__dict__.update(kwargs)
                inline_instances.append(inline)
                self.exclude.append(name)

        return inline_instances
