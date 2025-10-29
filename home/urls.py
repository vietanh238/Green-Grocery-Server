from django.urls import path
from .get_notification.views import GetNotificationsView
from .get_dashboard.views import GetDashboard

urlpatterns = [
    path('notifications/', GetNotificationsView.as_view()),
    path('get/dashboard/', GetDashboard.as_view())
]