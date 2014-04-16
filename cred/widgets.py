from django.forms.widgets import ClearableFileInput


class CredAttachmentInput(ClearableFileInput):
    template_with_clear = '<label class="force-inline" for="%(clear_checkbox_id)s">%(clear)s %(clear_checkbox_label)s</label>'
    url_markup_template = '{1}'
