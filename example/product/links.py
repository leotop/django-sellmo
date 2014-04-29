from sellmo import modules
from sellmo.api.decorators import link


@link(namespace=modules.product.namespace, capture=True)
def list(index=None, qty=None, **kwargs):
    return
    if index is None:
        index = 'product_price'
    if qty is None:
        qty = 9999999
    return {
        'index' : index,
        'qty' : qty
    }


@link(namespace=modules.product.namespace)
def list(products, query=None, **kwargs):
    if query:
        if ('sort', 'name') in query:
            products = products.order_by('name')
        elif ('sort', '-name') in query:
            products = products.order_by('-name')
    return {
        'products' : products
    }