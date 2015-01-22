from django.conf import settings
from django.contrib.sites.models import Site
from django.template import Context
from django.template.loader import get_template, render_to_string

from sellmo import modules
from sellmo.api.decorators import link


namespace = modules.checkout.namespace


def _get_context(**context):
    site = Site.objects.get_current()
    context.update({
        'settings': modules.settings.get_settings(),
        'request' : {
            'site' : site,
        },
        'url': 'http://{0}'.format(site.domain),
        'prefix': 'http://{0}'.format(site.domain),
        'STATIC_URL': 'http://{0}{1}'.format(site.domain, settings.STATIC_URL),
        'MEDIA_URL': 'http://{0}{1}'.format(site.domain, settings.MEDIA_URL),
    })

    return context


@link()
def render_order_confirmation_email(format, order, data, **kwargs):
    template = None
    if format == 'html':
        template = get_template('checkout/emails/order_confirmation.html')
    elif format == 'text':
        template = get_template('checkout/emails/order_confirmation.txt')

    if template:
        data = template.render(Context(_get_context(order=order)))
        return {
            'data' : data
        }


@link()
def render_order_notification_email(format, order, data, **kwargs):
    template = None
    if format == 'html':
        template = get_template('checkout/emails/order_notification.html')
    elif format == 'text':
        template = get_template('checkout/emails/order_notification.txt')

    if template:
        data = template.render(Context(_get_context(order=order)))
        return {
            'data' : data
        }


@link()
def render_shipping_notification_email(format, order, data, **kwargs):
    template = None
    if format == 'html':
        template = get_template('checkout/emails/shipping_notification.html')
    elif format == 'text':
        template = get_template('checkout/emails/shipping_notification.txt')

    if template:
        data = template.render(Context(_get_context(order=order)))
        return {
            'data' : data
        }


@link()
def render_invoice_report(order, internal, data, **kwargs):
    template = get_template('checkout/reports/invoice.html')
    data = template.render(Context(_get_context(order=order, internal=internal)))

    return {
        'data' : data
    }


@link()
def render_order_confirmation_report(order, internal, data, **kwargs):
    template = get_template('checkout/reports/order_confirmation.html')
    data = template.render(Context(_get_context(order=order, internal=internal)))

    return {
        'data' : data
    }

