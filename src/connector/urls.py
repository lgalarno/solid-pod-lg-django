from django.urls import path

from connector import views

app_name = 'connector'

urlpatterns = [
    path('connect/', views.connect_oidc, name="connect"),
    path('connect-webid/', views.connect_webid, name="connect-webid"),
    path('disconnect-webid/', views.disconnect_webid, name="disconnect-webid"),
    path('callback', views.oauth_callback, name="oidc-callback"),
    path('refesh-token/<int:pk>/', views.refresh_token, name="refesh-token"),
    #path('api/', include('oidc.api.urls', namespace="oidc-api")),
]
