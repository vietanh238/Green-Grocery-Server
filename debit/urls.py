from django.urls import path
from .get_customer.views import GetCustomerView
from .get_debit.views import GetDebitViews
from .create_customer.views import CreateCustomer
from .create_debit.views import CreateDebit
from .pay_debit.views import PayDebit
from .delete_customer.views import DeleteCustomer

urlpatterns = [
    path('get/customer/', GetCustomerView.as_view()),
    path('get/debit/', GetDebitViews.as_view()),
    path('create/customer/', CreateCustomer.as_view()),
    path('create/debit/', CreateDebit.as_view()),
    path('pay/debit/', PayDebit.as_view()),
    path('delete/customer/', DeleteCustomer.as_view())
]
