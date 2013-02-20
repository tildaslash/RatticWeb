from cred.models import Category

def base_template_reqs(request):
     return {'allcategories': Category.objects.all()}


