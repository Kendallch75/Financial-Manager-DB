from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import UserViewSet, AccountViewSet, CategoryViewSet, ServiceViewSet, MovementViewSet, ExchangeRateViewSet, AccountLimitViewSet, dashboard

router = DefaultRouter()
router.register(r'users', UserViewSet)
router.register(r'accounts', AccountViewSet)
router.register(r'categories', CategoryViewSet)
router.register(r'services', ServiceViewSet)
router.register(r'movements', MovementViewSet)
router.register(r'exchange-rates', ExchangeRateViewSet)
router.register(r'account-limits', AccountLimitViewSet)

urlpatterns = [
    path('dashboard/', dashboard),
    path('', include(router.urls)),
]
