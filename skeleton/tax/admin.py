from django.contrib import admin
from django.contrib.contenttypes.models import ContentType
from django.utils.translation import ugettext_lazy as _

from sellmo import modules
from sellmo.contrib.polymorphism.admin import PolymorphicParentModelAdmin

# Base admin for every tax subtype
class TaxAdminBase(admin.ModelAdmin):
    pass

# Admin for percent tax
class PercentTaxAdmin(TaxAdminBase):
    pass

# Admin for tax
class TaxAdmin(PolymorphicParentModelAdmin):
    base_model = modules.tax.Tax
    child_models = [
        (modules.tax.PercentTax, PercentTaxAdmin),
    ]

    polymorphic_list = True
    list_display = ['name']
    list_display_links = ['name']

    search_fields = ['name']

    def queryset(self, queryset):
        return modules.tax.Tax.objects.all()

    def get_child_type_choices(self):
        choices = []
        for model, _ in [(modules.tax.PercentTax, None),]:
            ct = ContentType.objects.get_for_model(model)
            choices.append((ct.id, model._meta.verbose_name))
        return choices

# Register admins
admin.site.register(modules.tax.Tax, TaxAdmin)

