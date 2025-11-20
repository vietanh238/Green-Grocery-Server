
from django.urls import path
from django.views.decorators.csrf import csrf_exempt
from .views import WebhookView
from .payment.views import CreatePaymentView
from .cash_payment.views import CashPaymentView
from .cancel_order.views import CancelOrderView, RefundOrderView

urlpatterns = [
    path("create/", CreatePaymentView.as_view(), name="payments-create"),
    path("delete/<str:pk>/", CreatePaymentView.as_view(), name="payments-delete"),
    path("webhook/", csrf_exempt(WebhookView.as_view()), name="payments-webhook"),
    path('cash/', CashPaymentView.as_view(), name='cash-payment'),
    path('cancel/<str:order_code>/', CancelOrderView.as_view(), name='cancel-order'),
    path('refund/<str:order_code>/', RefundOrderView.as_view(), name='refund-order'),
]
