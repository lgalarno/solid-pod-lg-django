from django.contrib.auth.decorators import login_required
from django.urls import path, include

from pod_registration import views


app_name = 'pod_registration'

urlpatterns = [
    path('dashboard/', login_required(views.dashboard), name="dashboard"),
    path('create-container/<int:pk>/', login_required(views.create_container), name="create_container"),
    path('create-resource/<int:pk>/', login_required(views.create_resource), name="create_resource"),
    path('delete-resource/<int:pk>/', login_required(views.delete_resource), name="delete_resource"),
    path('download-resource/<int:pk>/', login_required(views.download_resource), name="download_resource"),
    path('preview-resource/<int:pk>/', login_required(views.preview_resource), name="preview_resource"),
    path('update-resource/<int:pk>/', login_required(views.update_resource), name="update_resource"),
    path('upload-resource/<int:pk>/', login_required(views.upload_resource), name="upload_resource"),
    path('view-resource/<int:pk>/', login_required(views.view_resource), name="view_resource"),
    path('htmx-api/', include('pod_registration.htmx-api.urls', namespace="pod_registration-htmx-api")),
]
