from django.urls import path
from .views import CalendarView, CalendarSummaryView

urlpatterns = [
    path('', CalendarView.as_view(), name='calendar'),
    path('summary/', CalendarSummaryView.as_view(), name='calendar-summary'),
]

# Made with Bob
