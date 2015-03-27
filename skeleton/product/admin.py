from sellmo import modules
from sellmo.utils.forms import FormFactory

from sellmo.contrib.category.admin import (ProductCategoryListFilter,
                                                   ProductCategoriesMixin)
from sellmo.contrib.variation.admin import (VariantAttributeMixin,
                                                    ProductVariationMixin)
from sellmo.contrib.attribute.admin import ProductAttributeMixin
from sellmo.contrib.tax.forms import ProductTaxesForm

from django.contrib import admin
from django.db import models
from django.contrib.contenttypes.models import ContentType
from django.utils.translation import ugettext_lazy as _

from sorl.thumbnail import get_thumbnail

from extras.admin.polymorphism import PolymorphicParentModelAdmin, PolymorphicChildModelAdmin


class ProductQtyPriceInline(admin.TabularInline):
    model = modules.qty_pricing.ProductQtyPrice


class ProductFormFactory(FormFactory):
    def factory(self):
        class ProductForm(
                ProductVariationMixin.form,
                ProductAttributeMixin.form,
                ProductTaxesForm):
            pass
        return ProductForm


class ProductAdminBase(ProductCategoriesMixin, ProductAttributeMixin, ProductVariationMixin, PolymorphicChildModelAdmin):

    form = ProductFormFactory()

    inlines = [ProductQtyPriceInline]
    fieldsets = (
        (_("Product information"), {
            'fields': ('name', 'sku', 'main_image', 'short_description',)
        }),
        (_("Product pricing"), {
            'fields': ('taxes',)
        }),
        (_("Product availability"), {
            'fields': ('allow_backorders', 'supplier', 'min_backorder_time', 'max_backorder_time', 'stock',)
        }),
        (_("Store arrangement"), {
            'fields': ('slug', 'categories', 'primary_category', 'active', 'featured',)
        }),
    )

    filter_horizontal = ['categories']

    prepopulated_fields = {
        'slug' : ('name',),
    }

    raw_id_fields = ['primary_category']
    autocomplete_lookup_fields = {
        'fk': ['primary_category'],
    }


class VariantInline(VariantAttributeMixin, admin.StackedInline):

    fieldsets = (
        (_("Product information"), {
            'fields': ('name', 'sku', 'main_image', 'short_description',)
        }),
        (_("Store arrangement"), {
            'fields': ('slug',)
        }),
        (_("Product pricing"), {
            'fields': ('price_adjustment',)
        }),
    )


class ProductParentAdmin(PolymorphicParentModelAdmin):
    
    base_model = modules.product.Product
    
    polymorphic_list = False
    list_display = ['slug']
    list_display_links = ['slug']
    search_fields = ['slug']
    
    child_models = []
    

    list_display = ['thumbnail', 'name', 'active', 'featured', 'slug', 'sku', 'stock']
    list_display_links = ['name', 'slug']
    list_editable = ['active', 'featured']

    list_filter = [ProductCategoryListFilter, 'active', 'featured']
    search_fields = ['name', 'slug', 'sku']

    def get_queryset(self, queryset):
        return modules.product.Product.objects.variants(exclude=True)

    def thumbnail(self, instance):
        if instance.main_image:
            try:
                thumbnail = get_thumbnail(instance.main_image, '30x30', crop='center', quality=100)
                return '<img src="%s"/>' % (thumbnail.url)
            except IOError:
                pass
        return ''

    thumbnail.allow_tags = True
    thumbnail.short_description = _("thumbnail")


admin.site.register(modules.product.Product, ProductParentAdmin)


# Simple product

class SimpleVariantInline(VariantInline):
    model = modules.variation.SimpleProductVariant
    fk_name = 'product'


class SimpleProductAdmin(ProductAdminBase):
    base_model = modules.product.SimpleProduct
    inlines = ProductAdminBase.inlines + [SimpleVariantInline]
    
    
ProductParentAdmin.child_models += [
    (modules.product.SimpleProduct, SimpleProductAdmin)]