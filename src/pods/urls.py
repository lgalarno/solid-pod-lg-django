from django.contrib.auth.decorators import login_required
from django.urls import path, include

from pods import views


app_name = 'pods'

urlpatterns = [
    path('dashboard/', login_required(views.dashboard), name="dashboard"),
    path('view-resource/<int:pk>/', views.view_resource, name="view_resource"),
    path('create-resource/<int:pk>/', views.create_resource, name="create_resource"),
    path('update-resource/<int:pk>/', views.update_resource, name="update_resource"),
    path('delete-resource/<int:pk>/', views.delete_resource, name="delete_resource"),
    path('htmx-api/', include('pods.htmx-api.urls', namespace="pods-htmx-api")),
]
