from sellmo import modules
from sellmo.utils.forms import FormFactory
from sellmo.contrib.product.admin import (ProductParentAdminBase, 
                                                  ProductAdminBase)
from sellmo.contrib.category.admin import (ProductCategoryListFilter,
                                                   ProductCategoriesMixin)
from sellmo.contrib.variation.admin import (VariantAttributeMixin,
                                                    ProductVariationMixin)
from sellmo.contrib.attribute.admin import ProductAttributeMixin
from sellmo.contrib.tax.forms import ProductTaxesForm

from django import forms
from django.contrib import admin
from django.contrib.contenttypes.generic import GenericTabularInline
from django.db import models
from django.db.models import Q
from django.utils.translation import ugettext_lazy as _
from django.contrib.admin.sites import NotRegistered
from django.contrib.contenttypes.models import ContentType


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


class ProductAdmin(ProductCategoriesMixin, ProductAttributeMixin, ProductVariationMixin, ProductAdminBase):

    form = ProductFormFactory()

    inlines = [ProductQtyPriceInline]
    fieldsets = (
        (_("Product information"), {
            'fields': ('name', 'sku',)
        }),
        (_("Product pricing"), {
            'fields': ('taxes',)
        }),
        (_("Webshop arrangement"), {
            'fields': ('slug', 'categories', 'primary_category', 'active', 'featured')
        })
    )

    filter_horizontal = ['categories']
    
    prepopulated_fields = {
        'slug' : ('name',),
    }

    raw_id_fields = ['primary_category']
    autocomplete_lookup_fields = {
        'fk': ['primary_category'],
    }


class SimpleProductAdmin(ProductAdmin):
    inlines = ProductAdmin.inlines
    

class ProductParentAdmin(ProductParentAdminBase):
    child_models = [
        (modules.product.SimpleProduct, SimpleProductAdmin),

    ]
    polymorphic_list = False

    list_display = ['name', 'active', 'featured', 'slug', 'sku']
    list_display_links = ['name', 'slug']

    list_filter = [ProductCategoryListFilter, 'active', 'featured']
    search_fields = ['name', 'slug', 'sku']

    def queryset(self, queryset):
        return modules.product.Product.objects.variants(exclude=True)


admin.site.register(modules.product.Product, ProductParentAdmin)
