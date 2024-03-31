from django.urls import path, include

from . import views


app_name = 'pod_session'

urlpatterns = [
    path('connect/', views.connect_oidc, name="connect_oidc"),
    path('resource-form/', views.resource_form, name="resource_form"),
    path('resource-view/', views.resource_view, name="resource_view"),
    path('delete-resource/', views.delete_resource, name="delete_resource"),
]
