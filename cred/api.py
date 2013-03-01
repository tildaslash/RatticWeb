from django.db import models
from tastypie.authentication import SessionAuthentication
from tastypie.resources import ModelResource
from tastypie import fields
from cred.models import Cred, Tag

class TagResource(ModelResource):
    class Meta:
        queryset = Tag.objects.all()
        resource_name = 'tag'
        authentication = SessionAuthentication()

class CredResource(ModelResource):
    tags = fields.ToManyField(TagResource, 'tags', full=True)
    class Meta:
        queryset = Cred.objects.all()
        resource_name = 'cred'
        authentication = SessionAuthentication()
        
