
import os.path


from django.db import models
from django.utils.translation import ugettext_lazy as _

from sellmo import modules
from sellmo.api.decorators import load



def upload_image_to(instance, filename):
    return os.path.join('product', instance.slug, filename)



@load(before='finalize_product_Product')
def load_model():
    class Product(modules.product.Product):
        
        name = models.CharField(
            max_length=255,
            verbose_name=_("product name")
        )
        
        sku = models.CharField(
            max_length=80,
            blank=True,
            verbose_name=_("sku")
        )
        
        main_image = models.ImageField(
            upload_to=upload_image_to,
            max_length=255,
            blank=True,
            verbose_name=_("main image"),
            help_text=_(
                "Main image for this product."
            )
        )
        
        short_description = models.TextField(
            blank=True,
            verbose_name=_("short description")
        )
        
        full_description = models.TextField(
            blank=True,
            verbose_name=_("short description")
        )
        
        def __unicode__(self):
            return self.name
        

        class Meta(modules.product.Product.Meta):
            abstract = True

    modules.product.Product = Product
