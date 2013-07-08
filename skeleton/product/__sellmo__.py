from django.db import models
from django.utils.translation import ugettext_lazy as _

#

from sellmo import modules
from sellmo.api.decorators import load

# Set namespace for this app to 'product'
namespace = modules.product.namespace

# Configure the product app
# modules.product.prefix = 'yoururl'

@load(action='setup_variants', after='load_product_subtypes')
def setup_variants():
    # 
    # modules.variation.batch_buy_enabled = True
    modules.variation.register_product_subtype(modules.product.SimpleProduct)
    
@load(after='load_product_Product', before='finalize_product_Product')
def load_models():
    class Product(modules.product.Product):
        
        name = models.CharField(
            max_length = 120,
            verbose_name = _("name"),
            blank = False,
            
            # IMPORTANT !!! If we want to make variations work.
            null = True
        )
    
        sku = models.CharField(
            max_length = 60,
            verbose_name = _("sku"),
            blank = True,
            
            # IMPORTANT !!! If we want to make variations work.
            null = True
        )
        
        # Override default unicode convertion
        def __unicode__(self):
            if self.name:
                return self.name
            return super(Product, self).__unicode__()
    
        # IMPORTANT !!!
        class Meta:
            # App label needs to match this apps name
            # because we define this model as abstract.
            app_label = 'product'
            
            # Sellmo will make a concrete model at the
            # end of the boot cycle, this model needs to
            # be abstract in order to make polymorphism 
            # work and maintain a clean database schema.
            abstract = True
    
    modules.product.Product = Product