from django.core.management.base import BaseCommand, CommandError
from PIL import Image
from cred.models import CredIcon
import os

class Command(BaseCommand):
    help = 'Ensures there exists a user named "admin" with the password "rattic"'

    def handle(self, *args, **options):
        basepath = os.path.join('cred', 'static', 'rattic', 'img', 'credicons')
        spritepath = os.path.join('cred', 'static', 'rattic', 'img', 'sprite.png')

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
        curx = 0
        for (path, image) in images:
            name = os.path.basename(path).split('.', 1)[0]
            sprite.paste(image, (curx, 0), image)
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

        sprite.save(spritepath)
        
