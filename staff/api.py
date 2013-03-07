from django.db import models
from django.contrib.auth.models import User, Group

from tastypie import fields
from tastypie.authentication import SessionAuthentication, MultiAuthentication, ApiKeyAuthentication
from tastypie.resources import ModelResource
from tastypie.authorization import Authorization
from tastypie.exceptions import Unauthorized

from cred.models import Cred, Tag, CredAudit

## Auth
class RatticGroupAuthorization(Authorization):
    def read_list(self, object_list, bundle):
        # This assumes a ``QuerySet`` from ``ModelResource``.
        return object_list.filter(id__in=bundle.request.user.groups.all())

    def read_detail(self, object_list, bundle):
        # In auth groups? if not computer says no
        if bundle.obj in bundle.request.user.groups.all():
            return True
        else:
            raise Unauthorized("You are not allowed to do that")

    def create_list(self, object_list, bundle):
        return object_list

    def create_detail(self, object_list, bundle):
        if bundle.request.user.is_staff:
            return True

        raise Unauthorized("Only staff may create groups")

    def update_list(self, object_list, bundle):
        raise Unauthorized("Not yet implemented.")

    def update_detail(self, object_list, bundle):
        raise Unauthorized("Not yet implemented.")

    def delete_list(self, object_list, bundle):
        # Sorry user, no deletes for you!
        raise Unauthorized("Not yet implemented.")

    def delete_detail(self, object_list, bundle):
        raise Unauthorized("Not yet implemented.")


class GroupResource(ModelResource):
    class Meta:
        queryset = Group.objects.all()
        resource_name = 'group'
        authentication = MultiAuthentication(ApiKeyAuthentication(), SessionAuthentication())
        authorization = RatticGroupAuthorization()

