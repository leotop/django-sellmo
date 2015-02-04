from sellmo import modules
from sellmo.api.decorators import load


@load(before='finalize_product', after='finalize_product_Product')
def setup_variants():
    modules.variation.register_product_subtype(modules.product.SimpleProduct)