from django.core.management.base import BaseCommand, CommandError
from django.core.exceptions import ObjectDoesNotExist
from django.contrib.auth.models import User


class Command(BaseCommand):
    help = 'Ensures there exists a user named "admin" with the password "rattic"'

    def handle(self, *args, **options):
        try:
            u = User.objects.get(username='admin')
        except ObjectDoesNotExist:
            u = User(username='admin', email='admin@example.com')

        u.set_password('rattic')
        u.is_staff = True
        u.save()
