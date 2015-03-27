from sellmo import modules
from sellmo.core.reporting import reporter

from django.contrib import admin
from django.conf.urls import patterns, url
from django.core.urlresolvers import reverse
from django.http import HttpResponse
from django.utils.translation import ugettext_lazy as _

from extras.admin.reverse import ReverseModelAdmin


class PurchaseInline(admin.TabularInline):
    model = modules.store.Purchase
    extra = 0

    raw_id_fields = ['product']


class OrderMailInline(admin.TabularInline):
    model = modules.checkout.OrderMail
    extra = 0
    max_num = 0

    def message_type(self, obj):
        if obj.pk:
            return obj.status.message_type
    message_type.allow_tags = True

    def send(self, obj):
        if obj.pk:
            return obj.status.send
    send.allow_tags = True

    def send_to(self, obj):
        if obj.pk:
            return obj.status.send_to
    send_to.allow_tags = True

    def delivered(self, obj):
        if obj.pk:
            return obj.status.delivered
    delivered.allow_tags = True

    readonly_fields = ['send', 'message_type', 'send_to', 'delivered']


class OrderAdmin(ReverseModelAdmin):

    inlines = [PurchaseInline, OrderMailInline]

    inline_type = 'stacked'
    inline_reverse = ['shipment', 'payment'] + \
        ['{0}_address'.format(address) for address in 
         modules.customer.address_types]

    list_display = [
        'order', 'number', 'status', 'total_amount', 'paid', 'modified',
        'action_links']
    list_display_links = ['order']

    raw_id_fields = ['customer']

    def order(self, obj):
        return unicode(obj)

    def action_links(self, obj):
        links = []
        if reporter.can_report('invoice'):
            links.append(("<a href='{0}'>Print Invoice</a>"
                         .format(reverse(
                            'admin:checkout.invoice',
                            args=(obj.pk,)))))
        if reporter.can_report('order_confirmation'):
            links.append(("<a href='{0}'>Print Order Confirmation</a>"
                          .format(reverse(
                            'admin:checkout.order_confirmation',
                            args=(obj.pk,)))))

        return "<div>{0}</div>".format("&nbsp;/&nbsp;".join(links))

    action_links.allow_tags = True
    action_links.short_description = _("Actions")

    def invoice(self, request, id):
        order = modules.checkout.Order.objects.get(pk=id)
        invoice = reporter.get_report('invoice', context={
            'order': order
        })

        response = HttpResponse(content_type=invoice.mimetype)
        response.write(invoice.data)
        return response

    def order_confirmation(self, request, id):
        order = modules.checkout.Order.objects.get(pk=id)
        invoice = reporter.get_report('order_confirmation', context={
            'order': order
        })

        response = HttpResponse(content_type=invoice.mimetype)
        response.write(invoice.data)
        return response

    def get_urls(self):
        urls = super(OrderAdmin, self).get_urls()

        if reporter.can_report('invoice'):
            urls = (patterns('', 
                        url(r'^(.+)/invoice/$',
                        self.admin_site.admin_view(self.invoice),
                        name='checkout.invoice'),)
                    + urls)

        if reporter.can_report('order_confirmation'):
            urls = (patterns('', 
                        url(r'^(.+)/order_confirmation/$',
                        self.admin_site.admin_view(self.order_confirmation),
                        name='checkout.order_confirmation'),)
                    + urls)

        return urls


admin.site.register(modules.checkout.Order, OrderAdmin)
