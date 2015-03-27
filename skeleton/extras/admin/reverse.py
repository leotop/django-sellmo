from django.contrib.admin import ModelAdmin
from django.db.models import OneToOneField, ForeignKey
from django.contrib.admin.options import InlineModelAdmin
from django.contrib.admin.util import flatten_fieldsets
from django.forms import ModelForm
from django.forms.models import BaseModelFormSet, modelformset_factory
from django.utils.functional import curry


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
            # Will fix polymorphic behaviour
            queryset = obj.__class__.objects.filter(pk=obj.id)
        else:
            queryset = self.model.objects.none()

        if queryset.count() == 0:
            self.extra = 1
        super(ReverseInlineFormSet, self).__init__(
            data, files, prefix=prefix, queryset=queryset)
        
        f = instance._meta.get_field(self.parent_fk_name)
        if not f.blank and self.forms:
            self.forms[0].empty_permitted = False


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
        self.template = 'admin/edit_inline/{0}.html'.format(inline_type)
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
            
    def save_formset(self, request, form, formset, change):
        instances = formset.save()
        parent = form.instance
        if isinstance(formset, ReverseInlineFormSet) and instances:
            setattr(parent, formset.parent_fk_name, instances[0])
            parent.save()
    
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
