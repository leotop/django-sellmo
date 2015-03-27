from sellmo import modules

from django.contrib import admin


class ColorAdmin(admin.ModelAdmin):
    list_display = ['name', 'value']


class MultiColorAdmin(admin.ModelAdmin):
    list_display = ['name']


admin.site.register(modules.color.Color, ColorAdmin)
admin.site.register(modules.color.MultiColor, MultiColorAdmin)
