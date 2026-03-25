from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import TimeOffRequestViewSet

router = DefaultRouter()
router.register(r'requests', TimeOffRequestViewSet, basename='timeoffrequest')

urlpatterns = [
    path('', include(router.urls)),
]

# Made with Bob
