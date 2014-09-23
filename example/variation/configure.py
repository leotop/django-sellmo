from sellmo import modules
from sellmo.api.decorators import load


@load(action='setup_variants', after='load_product_subtypes')
def setup_variants():
    modules.variation.register_product_subtype(modules.product.SimpleProduct)