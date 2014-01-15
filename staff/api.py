from django.contrib.auth.models import Group
from django.conf import settings

from tastypie.authentication import SessionAuthentication, MultiAuthentication, ApiKeyAuthentication
from account.authentication import MultiApiKeyAuthentication
from tastypie.resources import ModelResource
from tastypie.authorization import Authorization
from tastypie.exceptions import Unauthorized


class RatticGroupAuthorization(Authorization):
    def read_list(self, object_list, bundle):
        return object_list

    def read_detail(self, object_list, bundle):
        return True

    def create_list(self, object_list, bundle):
        if settings.LDAP_ENABLED:
            raise Unauthorized("Please create groups in your LDAP server")

        if bundle.request.user.is_staff:
            return object_list

        raise Unauthorized("Only staff may create groups")

    def create_detail(self, object_list, bundle):
        if settings.LDAP_ENABLED:
            raise Unauthorized("Please create groups in your LDAP server")

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
    def obj_create(self, bundle, request=None, **kwargs):
        val = super(GroupResource, self).obj_create(bundle)
        bundle.request.user.groups.add(bundle.obj)
        return val

    def get_object_list(self, request):
        if request.user.is_staff:
            return super(GroupResource, self).get_object_list(request)
        else:
            return super(GroupResource, self).get_object_list(request).filter(id__in=request.user.groups.all())

    class Meta:
        queryset = Group.objects.all()
        always_return_data = True
        resource_name = 'group'
        authentication = MultiAuthentication(MultiApiKeyAuthentication(), SessionAuthentication())
        authorization = RatticGroupAuthorization()
