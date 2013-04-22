from django.contrib import admin
from django.contrib.contenttypes.models import ContentType
from django.utils.translation import ugettext_lazy as _

from sellmo import modules
from sellmo.contrib.contrib_category.admin import CategoryParentListFilter

#

class CategoryAdmin(admin.ModelAdmin):
	
	list_display = ['full_name', 'active', 'name', 'parent', 'slug']
	list_display_links = ['full_name', 'name']
	
	list_filter = [CategoryParentListFilter, 'active']
	search_fields = ['name']
	
	fieldsets = (
		(None, {
			'fields': ('name', 'parent', 'slug')
		}),
		(_("Display"), {
			'fields': ('active',)
		}),
	)
	
	raw_id_fields = ['parent']
	autocomplete_lookup_fields = {
	    'fk': ['parent'],
	}
	
	prepopulated_fields = {
		'slug' : ('name',),
	}
	
admin.site.register(modules.category.Category, CategoryAdmin)