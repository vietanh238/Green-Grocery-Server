# purchase_order/urls.py
from django.urls import path
from .create_po.views import CreatePurchaseOrderView
from .get_po.views import GetPurchaseOrdersView, GetPurchaseOrderDetailView
from .update_po.views import UpdatePurchaseOrderStatusView, DeletePurchaseOrderView
from .receive_po.views import ReceivePurchaseOrderView
from .send_email.views import SendPurchaseOrderEmailView

urlpatterns = [
    path('create/', CreatePurchaseOrderView.as_view(), name='create-purchase-order'),
    path('list/', GetPurchaseOrdersView.as_view(), name='get-purchase-orders'),
    path('detail/<int:po_id>/', GetPurchaseOrderDetailView.as_view(), name='get-purchase-order-detail'),
    path('update-status/<int:po_id>/', UpdatePurchaseOrderStatusView.as_view(), name='update-purchase-order-status'),
    path('delete/<int:po_id>/', DeletePurchaseOrderView.as_view(), name='delete-purchase-order'),
    path('receive/<int:po_id>/', ReceivePurchaseOrderView.as_view(), name='receive-purchase-order'),
    path('send-email/<int:po_id>/', SendPurchaseOrderEmailView.as_view(), name='send-purchase-order-email'),
]

