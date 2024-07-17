from django.contrib.auth.decorators import login_required
from django.urls import path, include

from pod_node import views


app_name = 'pod_node'

urlpatterns = [
    path('', views.pod_node, name="pod_node"),
    path('test/', views.test, name="test"),
    path('login/', views.login, name="login"),
    path('logout/', views.logout, name="logout"),
    path('sessions/', views.sessions, name="sessions"),
    path('login-callback/', views.login_callback, name="login_callback"),
    path('view-resource/', views.view_resource, name="view_resource"),
    path('preview-resource/', views.preview_resource, name="preview_resource"),
    path('download-resource/', views.download_resource, name="download_resource"),
    path('delete-resource/', views.delete_resource, name="delete_resource"),
]
