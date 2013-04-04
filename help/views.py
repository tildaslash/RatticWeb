from django.shortcuts import render
from django.conf import settings
from django.http import HttpResponseRedirect, Http404
from django.core.urlresolvers import reverse

import os


def markdown(request, page):
    if settings.HELP_SYSTEM_FILES is False:
        return render(request, 'help_nohelp.html', {})

    filename = os.path.join(settings.HELP_SYSTEM_FILES, page + '.md')
    if not os.path.exists(filename):
        raise Http404

    latestcopy = settings.PUBLIC_HELP_WIKI_BASE + page

    return render(request, 'help_markdown.html', {
        'file': filename,
        'latestlink': latestcopy,
    })


def home(request):
    return markdown(request, 'Home')
