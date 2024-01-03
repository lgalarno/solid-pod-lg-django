from django.urls import path, include

from . import views


app_name = 'pod_session'

urlpatterns = [
    path('connect/', views.connect_oidc, name="connect_oidc"),
    path('pod/', views.pod, name="pod"),
]
