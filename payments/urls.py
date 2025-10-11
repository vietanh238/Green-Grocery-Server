from django.urls import path
from .views import CreatePaymentView, WebhookView

urlpatterns = [
    path("create/", CreatePaymentView.as_view(), name="payments-create"),
    path("webhook/", WebhookView.as_view(), name="payments-webhook"),
]
