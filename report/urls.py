from django.urls import path
from .get_business_report.views import GetBusinessReport
from .inventory_report.views import (
    InventoryMovementReport,
    SupplierPerformanceReport,
    CustomerBehaviorReport
)

urlpatterns = [
    path('get/', GetBusinessReport.as_view()),
    path('inventory-movement/', InventoryMovementReport.as_view(), name='inventory-movement-report'),
    path('supplier-performance/', SupplierPerformanceReport.as_view(), name='supplier-performance-report'),
    path('customer-behavior/', CustomerBehaviorReport.as_view(), name='customer-behavior-report'),
]