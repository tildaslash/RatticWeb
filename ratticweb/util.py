from django.db import models
from django.core.management import call_command

def load_fixture(orm, file_name):
    original_get_model = models.get_model
    
    def get_model_southern_style(*args):
        try:
            return orm['.'.join(args)]
        except:
            return original_get_model(*args)
    
    models.get_model = get_model_southern_style
    
    call_command('loaddata', file_name)
    
    models.get_model = original_get_model

