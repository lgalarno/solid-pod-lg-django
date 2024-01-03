from django.contrib.auth.decorators import login_required
from django.urls import path

from . import views

app_name = 'pod_registration-htmx-api'

urlpatterns = [
    path('create-pod/', login_required(views.create_pod), name="create-pod"),
    path('delete-webid/<int:pk>/', login_required(views.delete_webid), name="delete-webid"),
    path('delete-pod/<int:pk>/', login_required(views.delete_pod), name="delete-pod"),
    path('create-issuer/', login_required(views.create_issuer), name="create-issuer"),
    path('issuer-list/', login_required(views.issuer_list), name="issuer-list"),
    path('pod-list/', login_required(views.pod_list), name="pod-list"),
    # path('webid-list/', login_required(views.webid_list), name="webid-list"),
]

