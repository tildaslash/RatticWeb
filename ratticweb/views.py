from django.shortcuts import redirect

def home(request):
    if request.user.is_authenticated():
        return redirect('/cred/list')
    else:
        return redirect('/account/login')

