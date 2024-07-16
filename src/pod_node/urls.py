from django.contrib.auth.decorators import login_required
from django.urls import path, include

from pod_node import views


app_name = 'pod_node'

urlpatterns = [
    path('', login_required(views.pod_node), name="pod_node"),
    path('test/', login_required(views.test), name="test"),
    path('login/', login_required(views.login), name="login"),
    path('logout/', login_required(views.logout), name="logout"),
    path('sessions/', login_required(views.sessions), name="sessions"),
    path('login-callback/', login_required(views.login_callback), name="login_callback"),
    path('view-resource/', login_required(views.view_resource), name="view_resource"),
]
