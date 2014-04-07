from __future__ import absolute_import

from .models import CredChangeQ
from ratticweb.celery import app
from django.core.mail import send_mail
from django.template import Context
from django.template.loader import render_to_string
from django.conf import settings


@app.task
def change_queue_emails():
    # Get everything on the Change Queue
    tochange = CredChangeQ.objects.all()

    tonotify = {}
    for ccq in tochange:
        cred = ccq.cred
        users = cred.group.user_set.filter(is_active=True)
        for user in users:
            if user in tonotify.keys():
                tonotify[user].append(cred)
            else:
                tonotify[user] = [cred, ]

    for user in tonotify.keys():
        c = Context({
            'user': user,
            'creds': tonotify[user],
            'host': settings.HOSTNAME,
        })

        text_content = render_to_string('mail/cred_change.txt', c)

        send_mail('RatticDB - Passwords requiring changes',
                  text_content,
                  settings.DEFAULT_FROM_EMAIL,
                  [user.email, ]
        )

    return True
