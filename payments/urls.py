
from django.urls import path
from django.views.decorators.csrf import csrf_exempt
from .views import WebhookView
from .payment.views import CreatePaymentView
from .cash_payment.views import CashPaymentView

urlpatterns = [
    path("create/", CreatePaymentView.as_view(), name="payments-create"),
    path("delete/<str:pk>/", CreatePaymentView.as_view(), name="payments-delete"),
    path("webhook/", csrf_exempt(WebhookView.as_view()), name="payments-webhook"),
    path('cash/', CashPaymentView.as_view(), name='cash-payment'),
]
