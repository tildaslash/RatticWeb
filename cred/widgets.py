from django.forms import Select
from django.utils.safestring import mark_safe
from django.forms.util import flatatt
from itertools import chain
from django.conf import settings

class CredImageSelect(Select):
    def render(self, name, value, attrs=None, choices=()):
        imgs = []
        imgstyle = ''
        for i in chain(self.choices, choices):
            imgs.append(self.render_image(i, name, imgstyle))
        imgdiv = '<div style="width: 200px">' + '\n'.join(imgs) + '</div>'
        basicselect = super(CredImageSelect, self).render(name, value, attrs, choices)
        return basicselect + mark_safe(imgdiv)

    def render_image(self, choice, name, imgstyle):
        onclick = ' onclick="$(\'select#id_' + name + '\').val(' + str(choice[0]) + ')"'
        img = '<img ' + imgstyle + onclick + ' title="' + choice[1] + '" src="' + settings.STATIC_URL + 'rattic/img/credicons/' + choice[1] + '.png" />'
        return img

