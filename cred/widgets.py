from django.forms.widgets import ClearableFileInput, HiddenInput
from django.utils.translation import ugettext_lazy as _
from templatetags.credicons import cred_icon
from django.utils.encoding import force_text
from django.utils.safestring import mark_safe


class CredAttachmentInput(ClearableFileInput):
    template_with_initial = '%(clear_template)s<br />%(input_text)s: %(input)s'
    template_with_clear = '<label class="force-inline" for="%(clear_checkbox_id)s">%(clear)s %(clear_checkbox_label)s</label>'
    url_markup_template = '{1}'


class CredIconChooser(HiddenInput):
    button_text = _('Choose')

    def render(self, name, value, attrs=None):
        logo = cred_icon(value, tagid='logodisplay')
        input = super(CredIconChooser, self).render(name, value, attrs)
        button = '<a href="#logoModal" role="button" class="btn" id="choosebutton" data-toggle="modal">%s</a>' % force_text(self.button_text)

        return mark_safe(logo + ' ' + button + input)
