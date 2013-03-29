from django.shortcuts import render
from django.conf import settings
from django.http import HttpResponseRedirect
from django.core.urlresolvers import reverse

import os

def markdown(request, page):
    if settings.HELP_SYSTEM_FILES == False:
        return render(request, 'help_nohelp.html', {})

    filename = os.path.join(settings.HELP_SYSTEM_FILES, page + '.md')
    return render(request, 'help_markdown.html', {'file': filename})

def home(request):
    return markdown(request, 'Home')

