from django.db import models
from django.forms import ModelForm
from django.contrib import admin
from django.contrib.auth.models import User

class UserProfile(models.Model):
  user = models.ForeignKey(User, unique=True)
  items_per_page = models.IntegerField(default=25)

  def __unicode__(self):
    return self.user.username

class UserProfileForm(ModelForm):
    class Meta:
        model = UserProfile
        exclude = ('user',)

# Attach the UserProfile object to the User
User.profile = property(lambda u: UserProfile.objects.get_or_create(user=u)[0])

admin.site.register(UserProfile)

