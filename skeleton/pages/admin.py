from django.contrib import admin
from django.contrib.contenttypes.models import ContentType
from django.utils.translation import ugettext_lazy as _

from pages.models import Page
from extras.admin.polymorphism import PolymorphicParentModelAdmin, PolymorphicChildModelAdmin


class PageAdminBase(PolymorphicChildModelAdmin):
    pass


class PageParentAdmin(PolymorphicParentModelAdmin):
    base_model = Page
    child_models = []

    polymorphic_list = True

    def get_queryset(self, queryset):
        return Page.objects.all()


admin.site.register(Page, PageParentAdmin)