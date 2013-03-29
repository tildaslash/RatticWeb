from django.shortcuts import render
from django.conf import settings
from django.http import HttpResponseRedirect
from django.core.urlresolvers import reverse

import os

def help_markdown(request, page):
    if settings.HELP_SYSTEM_FILES == False:
        return render(request, 'help_nohelp.html', {})

    filename = os.path.join(settings.HELP_SYSTEM_FILES, page + '.md')
    return render(request, 'help_markdown.html', {'file': filename})

def help_home(request):
    return help_markdown(request, 'Home')

