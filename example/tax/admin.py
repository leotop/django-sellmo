from sellmo import modules

from django.contrib import admin
from django.contrib.contenttypes.models import ContentType
from django.utils.translation import ugettext_lazy as _

from extras.admin.polymorphism import PolymorphicParentModelAdmin, PolymorphicChildModelAdmin


class TaxAdminBase(PolymorphicChildModelAdmin):
    filter_horizontal = ['products', 'categories']


class TaxParentAdmin(PolymorphicParentModelAdmin):
    base_model = modules.tax.Tax
    child_models = []

    polymorphic_list = True
    list_display = ['name']
    list_display_links = ['name']
    search_fields = ['name']

    def get_queryset(self, queryset):
        return modules.tax.Tax.objects.all()


admin.site.register(modules.tax.Tax, TaxParentAdmin)


# Percent tax

class PercentTaxAdmin(TaxAdminBase):
    base_model = modules.tax.Tax


TaxParentAdmin.child_models += [(modules.tax.PercentTax, PercentTaxAdmin)]
