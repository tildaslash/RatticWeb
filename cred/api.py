from tastypie import fields
from tastypie.authentication import SessionAuthentication, MultiAuthentication
from account.authentication import MultiApiKeyAuthentication
from tastypie.validation import FormValidation
from tastypie.resources import ModelResource
from tastypie.authorization import Authorization
from tastypie.exceptions import Unauthorized

from cred.models import Cred, Tag, CredAudit, TagForm


class CredAuthorization(Authorization):
    def read_list(self, object_list, bundle):
        # List views remove the deletes and historical credentials
        return object_list.filter(is_deleted=False, latest=None)

    def read_detail(self, object_list, bundle):
        # This audit should go somewhere else, is there a detail list function we can override?
        CredAudit(audittype=CredAudit.CREDPASSVIEW, cred=bundle.obj, user=bundle.request.user).save()
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


class TagAuthorization(Authorization):
    def read_list(self, object_list, bundle):
        return object_list

    def read_detail(self, object_list, bundle):
        return True

    def create_list(self, object_list, bundle):
        # Assuming their auto-assigned to ``user``.
        raise Unauthorized("Not yet implemented.")

    def create_detail(self, object_list, bundle):
        return True

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
        # Only show latest, not deleted and accessible credentials
        return Cred.objects.accessible(request.user, historical=True, deleted=True)

    def dehydrate(self, bundle):
        # Workaround for this tastypie issue:
        # https://github.com/toastdriven/django-tastypie/issues/201
        bundle.data['username'] = bundle.obj.username

        # Add a value indicating if something is on the change queue
        bundle.data['on_changeq'] = bundle.obj.on_changeq()

        # Unless you are viewing the details for a cred, hide the password
        if self.get_resource_uri(bundle) != bundle.request.path:
            del bundle.data['password']

        return bundle

    class Meta:
        queryset = Cred.objects.filter(is_deleted=False, latest=None)
        always_return_data = True
        resource_name = 'cred'
        excludes = ['username', 'is_deleted']
        authentication = MultiAuthentication(SessionAuthentication(), MultiApiKeyAuthentication())
        authorization = CredAuthorization()
        filtering = {
            'title': ('exact', 'contains', 'icontains'),
            'url': ('exact', 'startswith', ),
        }


class TagResource(ModelResource):
    # When showing a tag, show all the creds under it, that we are allowed to see
    creds = fields.ToManyField(CredResource,
        attribute=lambda bundle: Cred.objects.accessible(bundle.request.user).filter(tags=bundle.obj),
        null=True,
    )

    class Meta:
        queryset = Tag.objects.all()
        always_return_data = True
        filtering = {
            'name': ('exact', 'contains', 'icontains', 'startswith', 'istartswith'),
        }
        resource_name = 'tag'
        authentication = MultiAuthentication(SessionAuthentication(), MultiApiKeyAuthentication())
        authorization = TagAuthorization()
        validation = FormValidation(form_class=TagForm)
