from django.contrib import admin

from sellmo import modules

class ProductQtyPriceInline(admin.TabularInline):
    model = modules.qty_pricing.ProductQtyPrice