from django.urls import path
from .get_customer.views import GetCustomerView
from .get_debit.views import GetDebitViews

urlpatterns = [
    path('get/customer/', GetCustomerView.as_view()),
    path('get/debit/', GetDebitViews.as_view())
]
