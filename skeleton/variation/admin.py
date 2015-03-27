from sellmo import modules

from django.contrib import admin


class VariationAdmin(admin.ModelAdmin):
    list_display = ['description'{% if 'availability' in apps %}, 'stock'{% endif %}]
    list_editable = [{% if 'availability' in apps %}'stock'{% endif %}]


admin.site.register(modules.variation.Variation, VariationAdmin)
