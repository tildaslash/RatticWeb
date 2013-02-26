from cred.models import Tag, CredChangeQ
from django.db.models import Count

def base_template_reqs(request):
    cntx = {
        'alltags': Tag.objects.annotate(num_creds=Count('child_creds')).order_by('-num_creds')[:5],
        'pageurl': request.path,
    }

    if request.user.is_authenticated():
        cntx['changeqcount'] = CredChangeQ.objects.for_user(request.user).count()

    return cntx


