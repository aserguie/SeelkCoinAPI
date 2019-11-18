from rest_framework import routers
from .views import AlertViewSet

app_name = "alert"

router = routers.SimpleRouter(trailing_slash=False)
router.register("alerts", AlertViewSet, base_name="alerts")
router.register(r"users/(?P<user>\d+)/alerts", AlertViewSet, base_name="user_alert")

urlpatterns = router.urls
