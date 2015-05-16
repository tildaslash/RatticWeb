from django.db import models
from django.db.models import Q
from django.contrib import admin
from django.contrib.auth.models import User, Group
from django.utils.translation import ugettext_lazy as _
from django.forms.models import model_to_dict
from django.utils.timezone import now
from django.conf import settings

from ratticweb.util import DictDiffer, field_file_compare
from ssh_key import SSHKey
from fields import SizedFileField
from storage import CredAttachmentStorage


class Tag(models.Model):
    name = models.CharField(max_length=64, unique=True)

    def __unicode__(self):
        return self.name

    def visible_count(self, user):
        return Cred.objects.visible(user).filter(tags=self).count()


class CredIconAdmin(admin.ModelAdmin):
    list_display = ('name', 'filename')


class SearchManager(models.Manager):
    def visible(self, user, historical=False, deleted=False):
        usergroups = user.groups.all()
        qs = super(SearchManager, self).get_query_set()

        if not user.is_staff or not deleted:
            qs = qs.exclude(is_deleted=True, latest=None)

        if not historical:
            qs = qs.filter(latest=None)

        qs = qs.filter(Q(group__in=usergroups)
                     | Q(latest__group__in=usergroups)
                     | Q(groups__in=usergroups)
                     | Q(latest__groups__in=usergroups)).distinct()

        return qs

    def change_advice(self, user, grouplist=[]):
        logs = CredAudit.objects.filter(
            # Get a list of changes done
            Q(cred__group__in=grouplist, audittype=CredAudit.CREDCHANGE) |
            # Combined with a list of views from this user
            Q(cred__group__in=grouplist, audittype__in=[CredAudit.CREDVIEW, CredAudit.CREDPASSVIEW, CredAudit.CREDADD, CredAudit.CREDEXPORT], user=user)
        ).order_by('time', 'id')

        # Go through each entry in time order
        tochange = []
        for l in logs:
            # If this user viewed the password then change it
            if l.audittype in (CredAudit.CREDVIEW, CredAudit.CREDPASSVIEW, CredAudit.CREDADD, CredAudit.CREDEXPORT):
                tochange.append(l.cred.id)
            # If there was a change done not by this user, dont change it
            if l.audittype == CredAudit.CREDCHANGE and l.user != user:
                if l.cred.id in tochange:
                    tochange.remove(l.cred.id)

        # Fetch the list of credentials to change from the DB for the view
        return Cred.objects.filter(id__in=tochange)


class Cred(models.Model):
    METADATA = ('description', 'descriptionmarkdown', 'group', 'groups', 'tags', 'iconname', 'latest', 'id', 'modified', 'attachment_name', 'ssh_key_name')
    SORTABLES = ('title', 'username', 'group', 'id', 'modified')
    APP_SET = ('is_deleted', 'latest', 'modified', 'attachment_name', 'ssh_key_name')
    objects = SearchManager()

    # User changable fields
    title = models.CharField(verbose_name=_('Title'), max_length=64, db_index=True)
    url = models.URLField(verbose_name=_('URL'), blank=True, null=True, db_index=True)
    username = models.CharField(verbose_name=_('Username'), max_length=250, blank=True, null=True, db_index=True)
    password = models.CharField(verbose_name=_('Password'), max_length=250, blank=True, null=True)
    descriptionmarkdown = models.BooleanField(verbose_name=_('Markdown Description'), default=False, )
    description = models.TextField(verbose_name=_('Description'), blank=True, null=True)
    group = models.ForeignKey(Group, verbose_name=_('Group'))
    groups = models.ManyToManyField(Group, verbose_name=_('Groups'), related_name="child_creds", blank=True, null=True, default=None)
    tags = models.ManyToManyField(Tag, verbose_name=_('Tags'), related_name='child_creds', blank=True, null=True, default=None)
    iconname = models.CharField(verbose_name=_('Icon'), default='Key.png', max_length=64)
    ssh_key = SizedFileField(verbose_name=_('SSH key'), storage=CredAttachmentStorage(), max_upload_size=settings.RATTIC_MAX_ATTACHMENT_SIZE, null=True, blank=True, upload_to='not required')
    attachment = SizedFileField(verbose_name=_('Attachment'), storage=CredAttachmentStorage(), max_upload_size=settings.RATTIC_MAX_ATTACHMENT_SIZE, null=True, blank=True, upload_to='not required')

    # Application controlled fields
    is_deleted = models.BooleanField(default=False, db_index=True)
    latest = models.ForeignKey('Cred', related_name='history', blank=True, null=True, db_index=True)
    modified = models.DateTimeField(db_index=True)
    created = models.DateTimeField(auto_now_add=True)

    ssh_key_name = models.CharField(max_length=64, null=True, blank=True)
    attachment_name = models.CharField(max_length=64, null=True, blank=True)

    def save(self, *args, **kwargs):
        try:
            # Get a copy of the old object from the db
            old = Cred.objects.get(id=self.id)

            # Reset the primary key so Django thinks its a new object
            old.id = None

            # Set the latest on the old copy to the new copy
            old.latest = self

            # Create it in the DB
            old.save()

            # Add the tags to the old copy now that it exists
            for t in self.tags.all():
                old.tags.add(t)

            # Add the groups
            for g in self.groups.all():
                old.groups.add(g)

            # Lets see what was changed
            oldcred = model_to_dict(old)
            newcred = model_to_dict(self)
            diff = DictDiffer(newcred, oldcred).changed()

            # Ohhhkaaay, so the attachment field looks like its changed every
            # time, so we do a deep comparison, if the files match we remove
            # it from the list of changed fields.
            for field in ('attachment', 'ssh_key'):
                if field_file_compare(oldcred[field], newcred[field]):
                    diff = diff - set((field, ))

            # Check if some non-metadata was changed
            chg = diff - set(Cred.METADATA)
            cred_changed = len(chg) > 0

            # If the creds were changed update the modify date
            if cred_changed:
                self.modified = now()
        except Cred.DoesNotExist:
            # This just means its new cred, set the initial modified time
            self.modified = now()

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

    def is_owned_by(self, user):
        # Staff can do anything
        if user.is_staff:
            return True

        # If its the latest and in your group you can see it
        if not self.is_deleted and self.latest is None and self.group in user.groups.all():
            return True

        # If the latest is in your group you can see it
        if not self.is_deleted and self.latest is not None and self.latest.group in user.groups.all():
            return True

        return False

    def is_visible_by(self, user):
        # Staff can see anything
        if user.is_staff:
            return True

        # If its the latest and (in your group or it belongs to a viewer group you also belong to) you can see it
        if not self.is_deleted and self.latest is None and (self.group in user.groups.all() or any([g in user.groups.all() for g in self.groups.all()])):
            return True

        # If the latest is in your group you can see it
        if not self.is_deleted and self.latest is not None and (self.latest.group in user.groups.all() or any([g in user.groups.all() for g in self.latest.groups.all()])):
            return True

        return False

    def ssh_key_fingerprint(self):
        return SSHKey(self.ssh_key.read(), self.password).fingerprint()

    def __unicode__(self):
        return self.title.encode('utf-8')


class CredAdmin(admin.ModelAdmin):
    list_display = ('title', 'username', 'group')


class CredAudit(models.Model):
    CREDADD = 'A'
    CREDCHANGE = 'C'
    CREDMETACHANGE = 'M'
    CREDVIEW = 'V'
    CREDEXPORT = 'X'
    CREDPASSVIEW = 'P'
    CREDDELETE = 'D'
    CREDSCHEDCHANGE = 'S'
    CREDAUDITCHOICES = (
        (CREDADD, _('Added')),
        (CREDCHANGE, _('Changed')),
        (CREDMETACHANGE, _('Only Metadata Changed')),
        (CREDVIEW, _('Only Details Viewed')),
        (CREDEXPORT, _('Exported')),
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
        return self.filter(cred__in=Cred.objects.visible(user))


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
