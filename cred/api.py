from django.db import models
from django.contrib.auth.models import User

from tastypie import fields
from tastypie.authentication import SessionAuthentication, MultiAuthentication, ApiKeyAuthentication
from tastypie.resources import ModelResource
from tastypie.authorization import Authorization
from tastypie.exceptions import Unauthorized

from cred.models import Cred, Tag, CredAudit

## Auth
class RatticAuthorization(Authorization):
    def read_list(self, object_list, bundle):
        # This assumes a ``QuerySet`` from ``ModelResource``.
        return object_list.filter(group__in=bundle.request.user.groups.all())

    def read_detail(self, object_list, bundle):
        # In auth groups? if not computer says no
        if bundle.obj.group in bundle.request.user.groups.all():
            CredAudit(audittype=CredAudit.CREDVIEW, cred=bundle.obj, user=bundle.request.user).save()
            return True
        else:
            raise Unauthorized("Not yet implemented.")

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


class TagResource(ModelResource):
    class Meta:
        queryset = Tag.objects.all()
        resource_name = 'tag'
        authentication = MultiAuthentication(SessionAuthentication(), ApiKeyAuthentication())
        authorization  = RatticAuthorization()

class CredResource(ModelResource):
    tags = fields.ToManyField(TagResource, 'tags', full=True)
    class Meta:
        queryset = Cred.objects.all()
        resource_name = 'cred'
        authentication = MultiAuthentication(SessionAuthentication(), ApiKeyAuthentication())
        authorization = RatticAuthorization()

    def dehydrate(self, bundle):
        if self.get_resource_uri(bundle) != bundle.request.path:
            del bundle.data['password']
        return bundle

