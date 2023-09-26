from django.contrib.auth.decorators import login_required
from django.urls import path

from accounts import views
from .views import EditProfile

app_name = 'accounts'

urlpatterns = [
    path('login/', views.login_view, name="login"),
    path('logout/', login_required(views.logout_view), name="logout"),
    path('register/', views.register_view, name="register"),
    path('edit/', EditProfile.as_view(), name="EditProfile")
]
