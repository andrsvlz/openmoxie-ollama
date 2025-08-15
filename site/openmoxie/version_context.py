import os
from django.conf import settings

def moxie_version(request):
    with open(settings.BASE_DIR / 'VERSION') as f:
        version_string = f.read().strip()
    return {'moxie_version': version_string}
