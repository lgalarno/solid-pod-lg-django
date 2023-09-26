from django.contrib import admin

from .models import OpenIDprovider, SolidPod, StateSession

# Register your models here.
admin.site.register(OpenIDprovider)
admin.site.register(SolidPod)
admin.site.register(StateSession)
