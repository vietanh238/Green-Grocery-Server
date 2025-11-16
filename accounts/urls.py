from django.urls import path
from .login.views import LoginView, RegisterView
from .change_pass.views import ChangePasswordView

urlpatterns = [
    path('login/', LoginView.as_view()),
    path('change/password/', ChangePasswordView.as_view()),
    path('register/', RegisterView.as_view(), name='register'),
]