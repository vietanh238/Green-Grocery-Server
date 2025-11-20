from django.urls import path
from .views import (
    InventoryHistoryView,
    InventoryAdjustmentView,
    InventoryDamageView,
    InventoryLostView,
    InventoryReturnView,
    InventorySummaryView
)

urlpatterns = [
    # Inventory history for specific product
    path('history/<int:product_id>/', InventoryHistoryView.as_view(), name='inventory-history'),

    # Inventory adjustments
    path('adjust/', InventoryAdjustmentView.as_view(), name='inventory-adjust'),

    # Record damages
    path('damage/', InventoryDamageView.as_view(), name='inventory-damage'),

    # Record lost items
    path('lost/', InventoryLostView.as_view(), name='inventory-lost'),

    # Return items to stock
    path('return/', InventoryReturnView.as_view(), name='inventory-return'),

    # Inventory summary/report
    path('summary/', InventorySummaryView.as_view(), name='inventory-summary'),
]

