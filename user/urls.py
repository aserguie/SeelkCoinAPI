from django.urls import path
from rest_framework import routers
from .views import logout_view, registration_view, SelfUserViewSet, UserViewSet
from rest_framework.authtoken.views import obtain_auth_token


app_name = "user"

user_detail = SelfUserViewSet.as_view(
    {"get": "retrieve", "patch": "partial_update", "delete": "destroy"}
)

router = routers.SimpleRouter(trailing_slash=False)
router.register("users", UserViewSet)

urlpatterns = [
    path("me", user_detail, name="user_detail"),
    path("register", registration_view, name="register"),
    path("login", obtain_auth_token, name="login"),
    path("logout", logout_view, name="logout"),
] + router.urls
