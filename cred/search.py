from django.contrib.auth.models import User, Group
from django.db.models import Q
from django.http import Http404
from django.shortcuts import get_object_or_404

from models import Cred, CredChangeQ, Tag


# TODO: Move this to a ModelManager
def cred_search(user, cfilter='special', value='all', sortdir='ascending', sort='title', groups=[]):
    cred_list = Cred.objects.accessible(user)
    search_object = None

    # Tag based searching
    if cfilter == 'tag':
        tag = get_object_or_404(Tag, pk=value)
        cred_list = cred_list.filter(tags=tag)
        search_object = tag

    # Group based searching
    elif cfilter == 'group':
        group = get_object_or_404(Group, pk=value)
        if group not in user.groups.all():
            raise Http404
        cred_list = cred_list.filter(group=group)
        search_object = group

    # Standard search, substring in title
    elif cfilter == 'search':
        cred_list = cred_list.filter(title__icontains=value)
        search_object = value

    # Search for the history of a cred
    elif cfilter == 'history':
        cred = get_object_or_404(Cred, pk=value)
        cred_list = Cred.objects.accessible(user, historical=True).filter(Q(latest=value) | Q(id=value))
        search_object = cred

    # Change Advice
    elif cfilter == 'changeadvice':
        if not user.is_staff:
            raise Http404
        search_object = get_object_or_404(User, pk=value)

        if len(groups) > 0:
            groups = Group.objects.filter(id__in=groups)
        else:
            groups = Group.objects.all()

        cred_list = Cred.objects.change_advice(search_object, groups)

    # View all
    elif cfilter == 'special' and value == 'all':
        pass  # Do nothing, list is already all accessible passwords

    # Trash can
    elif cfilter == 'special' and value == 'trash':
        cred_list = Cred.objects.accessible(user, deleted=True).filter(is_deleted=True)

    # Change Queue
    elif cfilter == 'special' and value == 'changeq':
        q = Cred.objects.filter(credchangeq__in=CredChangeQ.objects.all())
        cred_list = cred_list.filter(id__in=q)

    # Otherwise, search is invalid. Rasie 404
    else:
        raise Http404

    # Sorting rules
    if sortdir == 'ascending' and sort in Cred.SORTABLES:
        cred_list = cred_list.order_by('latest', sort)
    elif sortdir == 'descending' and sort in Cred.SORTABLES:
        cred_list = cred_list.order_by('latest', '-' + sort)
    else:
        raise Http404

    return (search_object, cred_list)
