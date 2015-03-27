from django.contrib import admin

from sellmo import modules

from extras.admin.reverse import ReverseModelAdmin


class AddressInline(admin.StackedInline):
    model = modules.customer.Address


class CustomerAdmin(ReverseModelAdmin):
    inline_type = 'stacked'
    inline_reverse = ['{0}_address'.format(address)
                      for address in modules.customer.address_types]

    if modules.customer.auth_enabled:
        raw_id_fields = ['user']


admin.site.register(modules.customer.Customer, CustomerAdmin)
