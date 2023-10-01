from django.contrib.auth.decorators import login_required
from django.urls import path

from . import views

app_name = 'pods_htmx-api'

urlpatterns = [
    path('create-pod/', login_required(views.create_pod), name="create-pod"),
    path('delete-webid/<int:pk>/', login_required(views.delete_webid), name="delete-webid"),
    path('delete-pod/<int:pk>/', login_required(views.delete_pod), name="delete-pod"),
    path('create-provider/', login_required(views.create_provider), name="create-provider"),
]
