from django.db import models
from django.contrib.auth.models import User

from tastypie import fields
from tastypie.authentication import SessionAuthentication, MultiAuthentication, ApiKeyAuthentication
from tastypie.resources import ModelResource
from tastypie.authorization import Authorization
from tastypie.exceptions import Unauthorized

from cred.models import Cred, Tag, CredAudit

## Auth
class CredAuthorization(Authorization):
    def read_list(self, object_list, bundle):
        # This assumes a ``QuerySet`` from ``ModelResource``.
        return object_list

    def read_detail(self, object_list, bundle):
        # This audit should go somewhere else, is there a detail list function we can override?
        CredAudit(audittype=CredAudit.CREDVIEW, cred=bundle.obj, user=bundle.request.user).save()
        return True

    def create_list(self, object_list, bundle):
        # Assuming their auto-assigned to ``user``.
        raise Unauthorized("Not yet implemented.")

    def create_detail(self, object_list, bundle):
        raise Unauthorized("Not yet implemented.")

    def update_list(self, object_list, bundle):
        raise Unauthorized("Not yet implemented.")

    def update_detail(self, object_list, bundle):
        raise Unauthorized("Not yet implemented.")

    def delete_list(self, object_list, bundle):
        # Sorry user, no deletes for you!
        raise Unauthorized("Not yet implemented.")

    def delete_detail(self, object_list, bundle):
        raise Unauthorized("Not yet implemented.")


class CredResource(ModelResource):
    def get_object_list(self, request):
        return super(CredResource, self).get_object_list(request).filter(group__in=request.user.groups.all())

    def dehydrate(self, bundle):
        bundle.data['username'] = bundle.obj.username
        if self.get_resource_uri(bundle) != bundle.request.path:
            del bundle.data['password']
        return bundle

    class Meta:
        queryset = Cred.objects.filter(is_deleted=False, latest=None)
        resource_name = 'cred'
        excludes = ['username', 'is_deleted']
        authentication = MultiAuthentication(SessionAuthentication(), ApiKeyAuthentication())
        authorization = CredAuthorization()

class TagResource(ModelResource):
    creds = fields.ToManyField(CredResource,
                               attribute=lambda bundle: Cred.objects.accessable(bundle.request.user).filter(tags=bundle.obj),
                               full=True,
                               null=True)
    class Meta:
        queryset = Tag.objects.all()
        resource_name = 'tag'
        authentication = MultiAuthentication(SessionAuthentication(), ApiKeyAuthentication())

