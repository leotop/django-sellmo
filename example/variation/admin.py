from sellmo import modules

from django.contrib import admin


class VariationAdmin(admin.ModelAdmin):
    list_display = ['description', 'stock']
    list_editable = ['stock']


admin.site.register(modules.variation.Variation, VariationAdmin)
