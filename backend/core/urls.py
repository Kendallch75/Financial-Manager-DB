from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    UserViewSet,
    AccountViewSet,
    CategoryViewSet,
    ServiceViewSet,
    MovementViewSet,
    ExchangeRateViewSet,
    AccountLimitViewSet,
    dashboard,
    login_view,
    register_view,
    logout_view,
    me_view,
)

router = DefaultRouter()
router.register(r"users", UserViewSet, basename="users")
router.register(r"accounts", AccountViewSet, basename="accounts")
router.register(r"categories", CategoryViewSet, basename="categories")
router.register(r"services", ServiceViewSet, basename="services")
router.register(r"movements", MovementViewSet, basename="movements")
router.register(r"exchange-rates", ExchangeRateViewSet, basename="exchange-rates")
router.register(r"account-limits", AccountLimitViewSet, basename="account-limits")

urlpatterns = [
    path("auth/login/", login_view),
    path("auth/register/", register_view),
    path("auth/logout/", logout_view),
    path("auth/me/", me_view),
    path("dashboard/", dashboard),
    path("", include(router.urls)),
]
