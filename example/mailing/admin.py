from sellmo import modules

from django.contrib import admin


class MailStatusAdmin(admin.ModelAdmin):

    list_display = ['delivered', 'message_type', 'send',
                    'send_to', 'message_reference', 'failure_message']
    list_display_links = ['message_reference']


admin.site.register(modules.mailing.MailStatus, MailStatusAdmin)
