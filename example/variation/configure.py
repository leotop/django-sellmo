from sellmo import modules
from sellmo.api.decorators import load


@load(after='product_subtypes_loaded')
@load(before='variation_subtypes_loaded')
def setup_variants():
    modules.variation.register_product_subtype(modules.product.SimpleProduct)