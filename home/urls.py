from django.urls import path
from .get_notification.views import GetNotificationsView

urlpatterns = [
    path('notifications/', GetNotificationsView.as_view())
]