from sellmo import modules

from django.contrib import admin
from django.contrib.contenttypes.models import ContentType
from django.utils.translation import ugettext_lazy as _

from extras.admin.polymorphism import PolymorphicParentModelAdmin, PolymorphicChildModelAdmin


class DiscountAdminBase(PolymorphicChildModelAdmin):
    filter_horizontal = ['products', 'categories']


class DiscountParentAdmin(PolymorphicParentModelAdmin):
    base_model = modules.discount.Discount
    child_models = []

    polymorphic_list = True
    list_display = ['name']
    list_display_links = ['name']
    search_fields = ['name']

    def get_queryset(self, queryset):
        return modules.discount.Discount.objects.all()


class DiscountGroupAdmin(admin.ModelAdmin):
    pass


if modules.discount.user_discount_enabled:
    admin.site.register(modules.discount.DiscountGroup, DiscountGroupAdmin)
admin.site.register(modules.discount.Discount, DiscountParentAdmin)


# Percent discount

class PercentDiscountAdmin(DiscountAdminBase):
    base_model = modules.discount.Discount


DiscountParentAdmin.child_models += [(modules.discount.PercentDiscount, PercentDiscountAdmin)]
