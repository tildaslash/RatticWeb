from django.db import models
from django.contrib import admin
from django.contrib.auth.models import User, Group
from django.forms import ModelForm

class Category(models.Model):
    name = models.CharField(max_length=64)
    parent = models.ForeignKey('Category', related_name='child', null=True, blank=True)

    def __unicode__(self):
        return self.name
        
class CatForm(ModelForm):
    class Meta:
        model = Category

class Cred(models.Model):
    METADATA = ('description', 'group', 'category')
    title = models.CharField(max_length=64)
    username = models.CharField(max_length=250, blank=True, null=True)
    password = models.CharField(max_length=250)
    description = models.TextField(blank=True, null=True)
    group = models.ForeignKey(Group)
    category = models.ForeignKey(Category, blank=True, null=True, default=None)

    def __unicode__(self):
        return self.title

class CredForm(ModelForm):
    class Meta:
        model = Cred

class CredAdmin(admin.ModelAdmin):
    list_display = ('title', 'username', 'group')

class CredAudit(models.Model):
    CREDADD = 'A'
    CREDCHANGE = 'C'
    CREDMETACHANGE = 'M'
    CREDVIEW = 'V'
    CREDAUDITCHOICES = (
        (CREDADD, 'Credential Added'),
        (CREDCHANGE, 'Credential Change'),
        (CREDMETACHANGE, 'Credential Metadata change'),
        (CREDVIEW, 'Credential View'),
    )

    audittype = models.CharField(max_length=1, choices=CREDAUDITCHOICES)
    cred = models.ForeignKey(Cred, related_name='logs')
    user = models.ForeignKey(User, related_name='credlogs')
    time = models.DateTimeField(auto_now_add=True)

class CredAuditAdmin(admin.ModelAdmin):
    list_display = ('audittype', 'user', 'cred', 'time')

admin.site.register(CredAudit, CredAuditAdmin)
admin.site.register(Cred, CredAdmin)
admin.site.register(Category)
