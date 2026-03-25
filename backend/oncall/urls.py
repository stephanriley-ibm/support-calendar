from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import HolidayViewSet, OnCallShiftViewSet, DayInLieuViewSet

router = DefaultRouter()
router.register(r'holidays', HolidayViewSet, basename='holiday')
router.register(r'shifts', OnCallShiftViewSet, basename='oncallshift')
router.register(r'days-in-lieu', DayInLieuViewSet, basename='dayinlieu')

urlpatterns = [
    path('', include(router.urls)),
]

# Made with Bob
