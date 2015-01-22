from sellmo import modules
from sellmo.api.decorators import link


@link(namespace=modules.customer.namespace, capture=True)
def process_customer(data=None, **kwargs):
    if data and 'user-email' in data:
        data = data.copy()
        data['customer-email'] = data['user-email']

    return {
        'data': data
    }