from sellmo import modules
from sellmo.api.decorators import load

# Set namespace for this app to 'product'
namespace = modules.product.namespace

# Configure the product app
# modules.product.prefix = 'yoururl'

@load(action='setup_variants', after='load_subtypes')
def setup_variants():
	# 
	# modules.variation.batch_buy_enabled = True
	modules.variation.custom_options_enabled = True
	modules.variation.register_product_subtype(modules.product.SimpleProduct)