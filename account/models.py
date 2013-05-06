from django.db import models
from django import forms
from django.forms import ModelForm, SelectMultiple
from django.contrib import admin
from django.contrib.auth.models import User
from django.contrib.auth.forms import SetPasswordForm
from django.db.models.signals import pre_save
from django.dispatch import receiver
from django.utils.timezone import now

from cred.models import Tag


class LDAPPassChangeForm(SetPasswordForm):
    old_password = forms.CharField(label="Old password", widget=forms.PasswordInput)

    def clean_old_password(self):
        from django_auth_ldap.backend import LDAPBackend

        old_password = self.cleaned_data["old_password"]
        u = LDAPBackend().authenticate(self.user.username, old_password)
        if u is None:
            raise forms.ValidationError("Incorrect password")
        return old_password

    def save(self):
        old_password = self.cleaned_data["old_password"]
        new_password = self.cleaned_data["new_password1"]

        conn = self.user.ldap_user._get_connection()
        conn.simple_bind_s(self.user.ldap_user.dn, old_password.encode('utf-8'))
        conn.passwd_s(self.user.ldap_user.dn, old_password.encode('utf-8'), new_password.encode('utf-8'))

        return self.user

LDAPPassChangeForm.base_fields.keyOrder = ['old_password', 'new_password1', 'new_password2']


class UserProfile(models.Model):
    user = models.ForeignKey(User, unique=True)
    items_per_page = models.IntegerField(default=25)
    favourite_tags = models.ManyToManyField(Tag, blank=True)
    password_changed = models.DateTimeField(default=now)

    def __unicode__(self):
        return self.user.username


class UserProfileForm(ModelForm):
    class Meta:
        model = UserProfile
        exclude = ('user', 'password_changed',)
        widgets = {
            'favourite_tags': SelectMultiple(attrs={'class': 'chzn-select'}),
        }

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
