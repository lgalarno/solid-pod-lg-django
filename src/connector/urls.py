from django.urls import path

from connector import views

app_name = 'connector'

urlpatterns = [
    path('connect/', views.connect_oidc, name="connect"),
    path('callback', views.oauth_callback, name="oidc-callback"),
    path('refesh-token/<int:pk>/', views.refresh_token, name="refesh-token"),
    #path('api/', include('oidc.api.urls', namespace="oidc-api")),
]
