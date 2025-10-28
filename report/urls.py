from django.urls import path
from .get_business_report.views import GetBusinessReport

urlpatterns = [
    path('get/', GetBusinessReport.as_view()),
]