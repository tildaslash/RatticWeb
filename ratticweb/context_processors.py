from cred.models import Tag

def base_template_reqs(request):
    return {'alltags': Tag.objects.all()}


