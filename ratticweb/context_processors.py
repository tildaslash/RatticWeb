from cred.models import Tag, CredChangeQ

def base_template_reqs(request):
    cntx = {'alltags': Tag.objects.all(),}

    if request.user.is_authenticated():
        cntx['changeqcount'] = CredChangeQ.objects.for_user(request.user).count()

    return cntx


