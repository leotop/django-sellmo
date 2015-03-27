from sellmo import modules
from sellmo.contrib.category.admin import CategoryAdminBase, CategoryParentListFilter

from django.contrib import admin
from django.utils.translation import ugettext_lazy as _


class CategoryAdmin(CategoryAdminBase):

    list_display = ['full_name', 'active', 'name', 'parent', 'slug']
    list_display_links = ['full_name', 'name']

    list_filter = [CategoryParentListFilter, 'active']
    search_fields = ['name']

    fieldsets = (
        (None, {
            'fields': ('name', 'parent', 'slug')
        }),
        (_("Display"), {
            'fields': ('active', 'sort_order')
        }),
    )

    def full_name(self, instance):
        return instance.full_name
    full_name.short_description = _("full name")

    def full_slug(self, instance):
        return instance.full_slug
    full_slug.short_description = _("full slug")

    raw_id_fields = ['parent']

    prepopulated_fields = {
        'slug': ('name',),
    }


admin.site.register(modules.category.Category, CategoryAdmin)
