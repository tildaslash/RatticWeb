from cred.models import Tag, CredChangeQ
from django.db.models import Count
from django.conf import settings

def base_template_reqs(request):
    cntx = {
        'pageurl': request.path,
    }

    if settings.HELP_SYSTEM_FILES:
        cntx['helplinks'] = True
    else:
        cntx['helplinks'] = False

    if request.user.is_authenticated():
        cntx['changeqcount'] = CredChangeQ.objects.for_user(request.user).count()
        cntx['alltags'] = Tag.objects.annotate(num_creds=Count('child_creds')).order_by('-num_creds')[:request.user.profile.tags_on_sidebar]
    else:
        cntx['alltags'] = []

    return cntx


