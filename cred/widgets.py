from django.forms.widgets import ClearableFileInput


class CredAttachmentInput(ClearableFileInput):
    template_with_initial = '%(clear_template)s<br />%(input_text)s: %(input)s'
    template_with_clear = '<label class="force-inline" for="%(clear_checkbox_id)s">%(clear)s %(clear_checkbox_label)s</label>'
    url_markup_template = '{1}'
