from django import forms
from django.utils.translation import ugettext_lazy as _
from django.forms import ModelForm, SelectMultiple, Select, PasswordInput

import paramiko
from ssh_key import SSHKey
from models import Cred, Tag, Group
from widgets import CredAttachmentInput, CredIconChooser


class ExportForm(forms.Form):
    password = forms.CharField(widget=forms.PasswordInput(
        attrs={'class': 'btn-password-visibility'}
    ))


class TagForm(ModelForm):
    class Meta:
        model = Tag


class CredForm(ModelForm):
    def __init__(self, requser, *args, **kwargs):
        # Check if a new attachment was uploaded
        self.changed_ssh_key = len(args) > 0 and args[1].get('ssh_key', None) is not None
        self.changed_attachment = len(args) > 0 and args[1].get('attachment', None) is not None

        super(CredForm, self).__init__(*args, **kwargs)

        # Limit the group options to groups that the user is in
        self.fields['group'].queryset = Group.objects.filter(user=requser)

        self.fields['group'].label = _('Owner Group')
        self.fields['groups'].label = _('Viewers Groups')

        # Make the URL invalid message a bit more clear
        self.fields['url'].error_messages['invalid'] = _("Please enter a valid HTTP/HTTPS URL")

    def save(self, *args, **kwargs):
        # Get the filename from the file object
        if self.changed_attachment:
            self.instance.attachment_name = self.cleaned_data['attachment'].name
        if self.changed_ssh_key:
            self.instance.ssh_key_name = self.cleaned_data['ssh_key'].name

        # Call save upstream to save the object
        super(CredForm, self).save(*args, **kwargs)

    def clean_ssh_key(self):
        if self.cleaned_data.get("ssh_key") is not None:
            got = self.cleaned_data['ssh_key'].read()
            self.cleaned_data['ssh_key'].seek(0)
            try:
                SSHKey(got, self.cleaned_data['password']).key_obj
            except paramiko.ssh_exception.SSHException as error:
                raise forms.ValidationError(error)
        return self.cleaned_data['ssh_key']

    class Meta:
        model = Cred
        # These field are not user configurable
        exclude = Cred.APP_SET
        widgets = {
            # Use chosen for the tag field
            'tags': SelectMultiple(attrs={'class': 'rattic-tag-selector'}),
            'group': Select(attrs={'class': 'rattic-group-selector'}),
            'groups': SelectMultiple(attrs={'class': 'rattic-group-selector'}),
            'password': PasswordInput(render_value=True, attrs={'class': 'btn-password-generator btn-password-visibility'}),
            'ssh_key': CredAttachmentInput,
            'attachment': CredAttachmentInput,
            'iconname': CredIconChooser,
        }
