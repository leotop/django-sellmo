from django import forms
from django.core.exceptions import ValidationError
from django.utils.translation import ugettext_lazy as _


class ContactForm(forms.Form):

    name = forms.CharField(
        label = _("Name"),
    )
    email = forms.EmailField(
        label = _("E-mail")
    )

    message = forms.CharField(
        widget = forms.Textarea(attrs={'rows' : 4}),
        label = _("Message")
    )