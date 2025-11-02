from django.urls import path
from .get_notification.views import GetNotificationsView
from .get_dashboard.views import GetDashboard
from .get_user_profile.views import GetUserProfile
from .get_user_profile.views import QuickSearch

urlpatterns = [
    path('notifications/', GetNotificationsView.as_view()),
    path('get/dashboard/', GetDashboard.as_view()),
    path('user/profile/', GetUserProfile.as_view()),
    path('quick/search/', QuickSearch.as_view())
]