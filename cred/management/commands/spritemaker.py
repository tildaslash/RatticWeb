import os
import json

from django.core.management.base import BaseCommand
from django.conf import settings

from cred.icon import make_sprite


class Command(BaseCommand):
    help = 'Creates sprite files'

    def handle(self, *args, **options):
        basepath = os.path.join('cred', 'static', settings.CRED_ICON_BASEDIR)
        spritepath = os.path.join('cred', 'static', settings.CRED_ICON_SPRITE)
        jsonpath = os.path.join('cred', settings.CRED_ICON_JSON)
        csspath = os.path.join(settings.CRED_ICON_CSS)

        (data, sprite, css) = make_sprite(basepath)

        sprite.save(spritepath)
        with open(jsonpath, 'w') as jsonfile:
            jsonfile.write(json.dumps(data))
        with open(csspath, 'w') as cssfile:
            cssfile.write(css)
