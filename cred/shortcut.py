from django.shortcuts import render
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger


def render_credlist(request, credlist, title='All passwords'):
    # Paginate the credlist
    paginator = Paginator(credlist, request.user.profile.items_per_page)
    page = request.GET.get('page')
    try:
        cred = paginator.page(page)
    except PageNotAnInteger:
        cred = paginator.page(1)
    except EmptyPage:
        cred = paginator.page(paginator.num_pages)

    # Show the template
    return render(request, 'cred_list.html', {
        'credlist': cred,
        'credtitle': title,
    })
