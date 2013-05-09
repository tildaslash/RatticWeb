from django.core.management.base import BaseCommand
from PIL import Image
from cred.models import CredIcon
import os
import json


class Command(BaseCommand):
    help = 'Ensures there exists a user named "admin" with the password "rattic"'

    def handle(self, *args, **options):
        basepath = os.path.join('cred', 'static', 'rattic', 'img', 'credicons')
        spritepath = os.path.join('cred', 'static', 'rattic', 'img', 'sprite.png')
        jsonpath = os.path.join('cred', 'static', 'rattic', 'img', 'sprite.json')

        maxwidth = 0
        maxheight = 0
        images = []
        for f in os.listdir(basepath):
            fullpath = os.path.join(basepath, f)
            image = Image.open(fullpath)
            images.append((fullpath, image))
            (width, height) = image.size
            maxwidth = max(width, maxwidth)
            maxheight = max(height, maxheight)

        sprite = Image.new('RGBA', (maxwidth * len(images), maxheight))
        spritejson = {}
        curx = 0
        for (path, image) in images:
            jsprite = {}
            fname = os.path.basename(path)
            name = fname.split('.', 1)[0]
            sprite.paste(image, (curx, 0), image)
            jsprite['filename'] = fname
            jsprite['xoffset'] = curx
            jsprite['yoffset'] = 0
            try:
                icon = CredIcon.objects.get(name=name)
                icon.filename=os.path.basename(spritepath)
                icon.xoffset=curx
                icon.yoffset=0
                icon.save()
            except CredIcon.DoesNotExist:
                icon = CredIcon(name=name, filename=spritepath, xoffset=curx, yoffset=0)
                icon.save()
            curx += maxwidth
            spritejson[fname] = jsprite

        sprite.save(spritepath)
        with open(jsonpath, 'w') as jsonfile:
            jsonfile.write(json.dumps(spritejson))
