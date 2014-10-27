from django.db.models import FileField
from django import forms
from django.template.defaultfilters import filesizeformat
from django.utils.translation import ugettext_lazy as _
from south.modelsinspector import add_introspection_rules


add_introspection_rules([], ["^cred\.fields\.SizedFileField"])


class SizedFileField(FileField):
    def __init__(self, *args, **kwargs):
        # Get the upload size we were given
        self.max_upload_size = kwargs.pop('max_upload_size', None)

        super(SizedFileField, self).__init__(*args, **kwargs)

    def clean(self, *args, **kwargs):
        data = super(SizedFileField, self).clean(*args, **kwargs)

        file = data.file
        try:
            # If the file is bigger than we expected, give an error
            if file._size > self.max_upload_size:
                raise forms.ValidationError(_('File size must be under %(maximumsize)s. Current file size is %(currentsize)s.') % {'maximumsize': filesizeformat(self.max_upload_size), 'currentsize': filesizeformat(data.size)})
        except AttributeError:
            pass

        return data
