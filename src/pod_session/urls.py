from django.urls import path, include

from . import views


app_name = 'pod_session'

urlpatterns = [
    path('connect/', views.connect_oidc, name="connect_oidc"),
    path('resource-form/', views.resource_form, name="resource_form"),
    path('resource-view/', views.resource_view, name="resource_view"),
    path('resource-delete/', views.resource_delete, name="resource_delete"),
    path('resource-create/', views.resource_create, name="resource_create"),
]
