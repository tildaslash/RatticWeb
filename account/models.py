from django.db import models
from django.forms import ModelForm
from django.contrib import admin
from django.contrib.auth.models import User
from django.db.models.signals import pre_save
from django.dispatch import receiver
from datetime import datetime
from django.utils.timezone import now

class UserProfile(models.Model):
  user = models.ForeignKey(User, unique=True)
  items_per_page = models.IntegerField(default=25)
  tags_on_sidebar = models.IntegerField(default=5)
  password_changed = models.DateTimeField(default=now)

  def __unicode__(self):
    return self.user.username

class UserProfileForm(ModelForm):
    class Meta:
        model = UserProfile
        exclude = ('user', 'password_changed',)

# Attach the UserProfile object to the User
User.profile = property(lambda u: UserProfile.objects.get_or_create(user=u)[0])

@receiver(pre_save, sender=User)
def user_save_handler(sender, instance, **kwargs):
    try:
        olduser = User.objects.get(id=instance.id)
    except User.DoesNotExist:
        return
    if olduser.password != instance.password:
        p = instance.profile
        p.password_changed = now()
        p.save()

admin.site.register(UserProfile)

