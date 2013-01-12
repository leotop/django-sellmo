from django.contrib import admin
from django.utils.translation import ugettext_lazy as _

from sellmo.contrib.contrib_variation.models import Option, Variable, Attribute
from sellmo.contrib.contrib_variation.admin import AttributeTypeListFilterBase
from sellmo.contrib.polymorphism.admin import PolymorphicParentModelAdmin

from product.models import SimpleAttribute, ColorAttribute

class OptionInline(admin.TabularInline):
	model = Option
	raw_id_fields = ['attribute']
	sortable_field_name = 'sort_order'
	autocomplete_lookup_fields = {
		'fk': ['attribute'],
	}
	
	
class VariableAdmin(admin.ModelAdmin):
	inlines = [OptionInline]
	fieldsets = (
		(None, {
			'fields': ('name',)
		}),
	)

# Attribute subtype admin	
class SimpleAttributeAdmin(admin.ModelAdmin):
	fieldsets = (
		(None, {
			'fields': ('display', 'value')
		}),
	)
	
	prepopulated_fields = {
		'value' : ('display',),
	}
	
# Attribute subtype admin	
class ColorAttributeAdmin(admin.ModelAdmin):
	fieldsets = (
		(None, {
			'fields': ('name', 'color_code', 'value')
		}),
	)
	
	prepopulated_fields = {
		'value' : ('name',),
	}
	
# Implement the attribute type filter
class AttributeTypeListFilter(AttributeTypeListFilterBase):
	attribute_types = [SimpleAttribute, ColorAttribute]
	
# Attribute admin
class AttributeAdmin(PolymorphicParentModelAdmin):
	base_model = Attribute
	child_models = [
		(SimpleAttribute, SimpleAttributeAdmin),
		(ColorAttribute, ColorAttributeAdmin)
	]
	
	polymorphic_list = True
	list_display = ['display_value', 'value']
	list_display_links = ['display_value', 'value']
	list_filter = [AttributeTypeListFilter]
	
	# Show colors in the admin list
	def display_value(self, instance):
		if isinstance(instance, ColorAttribute):
			return '<div style="width: 15px; height: 15px; background-color: #%s;"></div>' % (instance.color_code)
		return unicode(instance)	
	display_value.allow_tags = True
	display_value.short_description = _("display value")