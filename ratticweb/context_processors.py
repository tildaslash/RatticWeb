from cred.models import Tag, CredChangeQ

def base_template_reqs(request):
    return {'alltags': Tag.objects.all(),
            'changeqcount': CredChangeQ.objects.all().count(),
           }


