from django.db import models
from django.contrib import admin
from django.contrib.auth.models import Group
from django.forms import ModelForm

class Cred(models.Model):
    title = models.CharField(max_length=64)
    username = models.CharField(max_length=250, blank=True, null=True)
    password = models.CharField(max_length=250)
    description = models.TextField(blank=True, null=True)
    group = models.ForeignKey(Group)

    def __unicode__(self):
        return self.title

class CredForm(ModelForm):
    class Meta:
        model = Cred

class CredAdmin(admin.ModelAdmin):
    list_display = ('title', 'username', 'group')

admin.site.register(Cred, CredAdmin)
