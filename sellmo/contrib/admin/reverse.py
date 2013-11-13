from django.contrib.admin import helpers, ModelAdmin
from django.contrib.admin.options import InlineModelAdmin
from django.contrib.admin.util import flatten_fieldsets
from django.db import transaction, models
from django.db.models import OneToOneField, ForeignKey
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
	def __init__(self, data=None, files=None, instance=None, prefix=None, queryset=None, save_as_new=False):
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
		super(ReverseInlineFormSet, self).__init__(data, files, prefix=prefix, queryset=queryset)

def reverse_inlineformset_factory(parent_model, model, parent_fk_name, form=ModelForm, fields=None, exclude=None, formfield_callback=lambda f:f.formfield()):
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
	'''
	Use the name and the help_text of the owning models field to
	render the verbose_name and verbose_name_plural texts.
	'''
	def __init__(self, parent_model, parent_fk_name, model, admin_site, inline_type):
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

	def get_formset(self, request, obj = None, **kwargs):
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
			"formfield_callback": curry(self.formfield_for_dbfield, request=request),
		}
		defaults.update(kwargs)
		return reverse_inlineformset_factory(self.parent_model,
											 self.model,
											 self.parent_fk_name,
											 **defaults)

class ReverseModelAdmin(ModelAdmin):
	
	def __init__(self, *args, **kwargs):
		super(ReverseModelAdmin, self).__init__(*args, **kwargs)
		if self.exclude is None:
			self.exclude = []
	
	def get_inline_instances(self, request, obj=None):
		inline_instances = super(ReverseModelAdmin, self).get_inline_instances(request, obj)
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
				inline = ReverseInlineModelAdmin(self.model, name, parent, self.admin_site, self.inline_type)
				if kwargs:
					inline.__dict__.update(kwargs)
				inline_instances.append(inline)
				self.exclude.append(name)
		
		return inline_instances