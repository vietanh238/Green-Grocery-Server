from django.urls import path
from .views import CreatePaymentView, WebhookView
from django.views.decorators.csrf import csrf_exempt

urlpatterns = [
    path("create/", CreatePaymentView.as_view(), name="payments-create"),
    path("delete/<str:pk>/", CreatePaymentView.as_view(), name="payments-delete"),
    path("webhook/", csrf_exempt(WebhookView.as_view()), name="payments-webhook"),
]
