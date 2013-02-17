from django.shortcuts import redirect

def home(request):
    if request.user.is_authenticated():
        return redirect('cred.views.list')
    else:
        return redirect('account.views.login')

