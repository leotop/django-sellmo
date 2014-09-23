from django.db import models
from django.utils.translation import ugettext_lazy as _

from sellmo import modules
from sellmo.api.decorators import load


@load(before='finalize_product_Product')
def load_model():
    class Product(modules.product.Product):

        name = models.CharField(
            max_length=255,
            verbose_name=_("product name")
        )

        sku = models.CharField(
            max_length=80,
            verbose_name=_("sku")
        )

        class Meta(modules.product.Product.Meta):
            abstract = True

    modules.product.Product = Product
