from django.contrib import admin

#

from sellmo import modules

#

class VariationAdmin(admin.ModelAdmin):
    list_display = ['id', 'deprecated']

admin.site.register(modules.variation.Variation, VariationAdmin)