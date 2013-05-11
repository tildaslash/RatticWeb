from django.conf import settings

from PIL import Image

import json
import os


def open_icons_in_folder(path):
    images = []
    for f in os.listdir(path):
        img = Image.open(os.path.join(path, f))
        images.append((f, img))

    return images


def build_layout(images):
    data = {}
    curx = 0
    cury = 0
    for (name, img) in images:
        (width, height) = img.size
        data[name] = {}
        data[name]['filename'] = name
        data[name]['xoffset'] = curx
        data[name]['yoffset'] = 0
        data[name]['width'] = width
        data[name]['height'] = height
        curx += width
        cury = max(cury, height)

    return (curx, cury, data)


def draw_sprite(images, data, size):
    sprite = Image.new('RGBA', size)
    for (name, img) in images:
        xloc = data[name]['xoffset']
        yloc = data[name]['yoffset']
        sprite.paste(img, (xloc, yloc), img)

    return sprite


def make_sprite(path):
    images = open_icons_in_folder(path)
    (mx, my, data) = build_layout(images)
    sprite = draw_sprite(images, data, (mx, my))

    return (data, sprite)


def get_icon_data():
    if get_icon_data._icons is None:
        get_icon_data._icons = json.loads(open(os.path.join('cred',
            settings.CRED_ICON_JSON), 'r').read())

    return get_icon_data._icons
get_icon_data._icons = None


def get_icon_list():
    return get_icon_data().keys()
