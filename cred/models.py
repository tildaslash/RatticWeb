from django.db import models
from django.contrib import admin
from django.contrib.auth.models import User, Group
from django.forms import ModelForm

class Tag(models.Model):
    name = models.CharField(max_length=64)

    def __unicode__(self):
        return self.name

class TagForm(ModelForm):
    class Meta:
        model = Tag

class CredManager(models.Manager):
    def for_user(self, user):
        return super(CredManager, self).get_query_set().filter(group__in=user.groups.all())

class Cred(models.Model):
    METADATA = ('description', 'group', 'tags')
    objects = CredManager()

    title = models.CharField(max_length=64)
    username = models.CharField(max_length=250, blank=True, null=True)
    password = models.CharField(max_length=250)
    description = models.TextField(blank=True, null=True)
    group = models.ForeignKey(Group)
    tags = models.ManyToManyField(Tag, related_name='child_creds', blank=True, null=True, default=None)

    def __unicode__(self):
        return self.title

class CredForm(ModelForm):
    def __init__(self,requser,*args,**kwargs):
        super (CredForm,self ).__init__(*args,**kwargs) # populates the post
        self.fields['group'].queryset = Group.objects.filter(user=requser)

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

    class Meta:
        get_latest_by = 'time'

class CredAuditAdmin(admin.ModelAdmin):
    list_display = ('audittype', 'user', 'cred', 'time')

class CredChangeQManager(models.Manager):
    def add_to_changeq(self, cred):
        return self.get_or_create(cred=cred)

    def for_user(self, user):
        return self.filter(cred__group__in=user.groups.all())

class CredChangeQ(models.Model):
    objects = CredChangeQManager()

    cred = models.ForeignKey(Cred, unique=True)
    time = models.DateTimeField(auto_now_add=True)

class CredChangeQAdmin(admin.ModelAdmin):
    list_display = ('cred', 'time')

admin.site.register(CredAudit, CredAuditAdmin)
admin.site.register(Cred, CredAdmin)
admin.site.register(Tag)
admin.site.register(CredChangeQ, CredChangeQAdmin)
