from sellmo import modules

from django.contrib import admin


class AttributeAdmin(admin.ModelAdmin):

    list_display = ['name', 'type', 'required', 'key']


class ValueAdmin(admin.ModelAdmin):

    list_display = ['product', 'attribute', 'value']
    list_filter = ['attribute']

    def value(self, obj):
        return obj.get_value()


admin.site.register(modules.attribute.Attribute, AttributeAdmin)
admin.site.register(modules.attribute.Value, ValueAdmin)
