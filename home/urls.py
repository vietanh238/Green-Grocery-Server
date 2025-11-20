from django.urls import path
from .get_notification.views import GetNotificationsView
from .get_dashboard.views import GetDashboardView
from .get_user_profile.views import GetUserProfile
from .get_user_profile.views import QuickSearch
from .get_history.views import TransactionHistoryView
from .ai.ai_views import (
    TrainAIModelView,
    GetProductForecastView,
    GetReorderRecommendationsView
)
urlpatterns = [
    path('notifications/', GetNotificationsView.as_view()),
    path('get/dashboard/', GetDashboardView.as_view()),
    path('user/profile/', GetUserProfile.as_view()),
    path('quick/search/', QuickSearch.as_view()),
    path('transactions/history/', TransactionHistoryView.as_view(), name='transaction-history'),
    path('ai/train/', TrainAIModelView.as_view(), name='train-ai-model'),
    path('ai/reorder-recommendations/',
         GetReorderRecommendationsView.as_view(), name='reorder-recommendations'),
    path('ai/forecast/<int:product_id>/',
         GetProductForecastView.as_view(), name='product-forecast'),
]
