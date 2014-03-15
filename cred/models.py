from django.db import models
from django.db.models import Q
from django.contrib import admin
from django.contrib.auth.models import User, Group
from django.forms import ModelForm, SelectMultiple
from django.utils.translation import ugettext_lazy as _


class Tag(models.Model):
    name = models.CharField(max_length=64, db_index=True)

    def __unicode__(self):
        return self.name

    def visible_count(self, user):
        return Cred.objects.accessible(user).filter(tags=self).count()


class TagForm(ModelForm):
    class Meta:
        model = Tag


class CredIconAdmin(admin.ModelAdmin):
    list_display = ('name', 'filename')


class SearchManager(models.Manager):
    def accessible(self, user, historical=False, deleted=False):
        usergroups = user.groups.all()
        qs = super(SearchManager, self).get_query_set()

        if not user.is_staff or not deleted:
            qs = qs.exclude(is_deleted=True, latest=None)

        if not historical:
            qs = qs.filter(latest=None)

        qs = qs.filter(Q(group__in=usergroups)
                     | Q(latest__group__in=usergroups))

        return qs

    def change_advice(self, user, grouplist=[]):
        logs = CredAudit.objects.filter(
            # Get a list of changes done
            Q(cred__group__in=grouplist, audittype=CredAudit.CREDCHANGE) |
            # Combined with a list of views from this user
            Q(cred__group__in=grouplist, audittype__in=[CredAudit.CREDVIEW, CredAudit.CREDPASSVIEW, CredAudit.CREDADD], user=user)
        ).order_by('time', 'id')

        # Go through each entry in time order
        tochange = []
        for l in logs:
            # If this user viewed the password then change it
            if l.audittype in (CredAudit.CREDVIEW, CredAudit.CREDPASSVIEW, CredAudit.CREDADD):
                tochange.append(l.cred.id)
            # If there was a change done not by this user, dont change it
            if l.audittype == CredAudit.CREDCHANGE and l.user != user:
                if l.cred.id in tochange:
                    tochange.remove(l.cred.id)

        # Fetch the list of credentials to change from the DB for the view
        return Cred.objects.filter(id__in=tochange)


class Cred(models.Model):
    METADATA = ('description', 'descriptionmarkdown', 'group', 'tags', 'iconname')
    objects = SearchManager()

    title = models.CharField(max_length=64, db_index=True)
    url = models.URLField(blank=True, null=True, db_index=True)
    username = models.CharField(max_length=250, blank=True, null=True)
    password = models.CharField(max_length=250)
    descriptionmarkdown = models.BooleanField(default=False, verbose_name=_('Markdown Description'))
    description = models.TextField(blank=True, null=True)
    group = models.ForeignKey(Group)
    tags = models.ManyToManyField(Tag, related_name='child_creds', blank=True, null=True, default=None)
    iconname = models.CharField(default='Key.png', max_length=64, verbose_name='Icon')
    is_deleted = models.BooleanField(default=False, db_index=True)
    latest = models.ForeignKey('Cred', related_name='history', blank=True, null=True, db_index=True)
    created = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        try:
            old = Cred.objects.get(id=self.id)
            old.id = None
            old.latest = self
            old.save()
            for t in self.tags.all():
                old.tags.add(t)
        except Cred.DoesNotExist:
            # This just means its new cred, ignore it
            pass
        super(Cred, self).save(*args, **kwargs)

    def delete(self):
        if not self.is_deleted:
            self.is_deleted = True
            self.save()
        else:
            super(Cred, self).delete()

    def on_changeq(self):
        return CredChangeQ.objects.filter(cred=self).exists()

    def is_latest(self):
        return self.latest is None

    def is_accessible_by(self, user):
        # Staff can see anything
        if user.is_staff:
            return True

        # If its the latest and in your group you can see it
        if not self.is_deleted and self.latest is None and self.group in user.groups.all():
            return True

        # If the latest is in your group you can see it
        if not self.is_deleted and self.latest is not None and self.latest.group in user.groups.all():
            return True

        return False

    def __unicode__(self):
        return self.title


class CredForm(ModelForm):
    def __init__(self, requser, *args, **kwargs):
        super(CredForm, self).__init__(*args, **kwargs)

        # Limit the group options to groups that the user is in
        self.fields['group'].queryset = Group.objects.filter(user=requser)

        # Make the URL invalid message a bit more clear
        self.fields['url'].error_messages['invalid'] = _("Please enter a valid HTTP/HTTPS URL")

    class Meta:
        model = Cred
        # These field are not user configurable
        exclude = ('is_deleted', 'latest')
        widgets = {
            # Use chosen for the tag field
            'tags': SelectMultiple(attrs={'class': 'rattic-tag-selector'}),
        }


class CredAdmin(admin.ModelAdmin):
    list_display = ('title', 'username', 'group')


class CredAudit(models.Model):
    CREDADD = 'A'
    CREDCHANGE = 'C'
    CREDMETACHANGE = 'M'
    CREDVIEW = 'V'
    CREDPASSVIEW = 'P'
    CREDDELETE = 'D'
    CREDSCHEDCHANGE = 'S'
    CREDAUDITCHOICES = (
        (CREDADD, _('Added')),
        (CREDCHANGE, _('Changed')),
        (CREDMETACHANGE, _('Only Metadata Changed')),
        (CREDVIEW, _('Only Details Viewed')),
        (CREDDELETE, _('Deleted')),
        (CREDSCHEDCHANGE, _('Scheduled For Change')),
        (CREDPASSVIEW, _('Password Viewed')),
    )

    audittype = models.CharField(max_length=1, choices=CREDAUDITCHOICES)
    cred = models.ForeignKey(Cred, related_name='logs')
    user = models.ForeignKey(User, related_name='credlogs')
    time = models.DateTimeField(auto_now_add=True)

    class Meta:
        get_latest_by = 'time'
        ordering = ('-time',)


class CredAuditAdmin(admin.ModelAdmin):
    list_display = ('audittype', 'user', 'cred', 'time')


class CredChangeQManager(models.Manager):
    def add_to_changeq(self, cred):
        return self.get_or_create(cred=cred)

    def for_user(self, user):
        return self.filter(cred__in=Cred.objects.accessible(user))


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
