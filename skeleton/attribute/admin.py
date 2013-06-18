from django.contrib import admin

#

from sellmo import modules
from sellmo.contrib.contrib_color.models import Color, MultiColor
from sellmo.contrib.contrib_attribute.admin import AttributeAdminMixin

#

class AttributeAdmin(AttributeAdminMixin, admin.ModelAdmin):
    pass
    
class ValueAdmin(admin.ModelAdmin):
    list_display = ['product', 'attribute', 'value']
    def value(self, obj):
        return obj.get_value()

admin.site.register(modules.attribute.Attribute, AttributeAdmin)
admin.site.register(modules.attribute.Value, ValueAdmin)
admin.site.register(Color)
admin.site.register(MultiColor)