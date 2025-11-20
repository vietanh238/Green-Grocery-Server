from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from django.db import transaction
from django.utils import timezone
from core.models import PurchaseOrder, Product
from core.services.inventory_service import InventoryService
from purchase_order.serializers import PurchaseOrderDetailSerializer


class ReceivePurchaseOrderView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, po_id):
        try:
            received_items = request.data.get('received_items', [])

            try:
                po = PurchaseOrder.objects.prefetch_related('items__product').get(
                    id=po_id, is_active=True
                )
            except PurchaseOrder.DoesNotExist:
                return Response({
                    'status': '2',
                    'response': {
                        'error_code': '002',
                        'error_message_us': 'Purchase order not found',
                        'error_message_vn': 'Không tìm thấy đơn đặt hàng'
                    }
                }, status=status.HTTP_404_NOT_FOUND)

            if po.status not in ['pending', 'approved']:
                return Response({
                    'status': '2',
                    'response': {
                        'error_code': '003',
                        'error_message_us': 'Invalid PO status for receiving',
                        'error_message_vn': 'Trạng thái đơn không cho phép nhận hàng'
                    }
                }, status=status.HTTP_400_BAD_REQUEST)

            with transaction.atomic():
                # Update received quantities and stock
                for received_item in received_items:
                    item_id = received_item.get('item_id')
                    received_qty = received_item.get('received_quantity', 0)

                    try:
                        po_item = po.items.get(id=item_id)
                    except:
                        continue

                    if received_qty > 0:
                        # Update PO item
                        po_item.received_quantity += received_qty
                        po_item.save()

                        # ✅ Use InventoryService để track nhập kho
                        try:
                            inventory_result = InventoryService.import_stock(
                                product_id=po_item.product.id,
                                quantity=received_qty,
                                unit_price=po_item.unit_price,
                                reference_type='purchase_order',
                                reference_id=po.id,
                                note=f'Nhập hàng từ PO {po.po_code} - {po.supplier.name if po.supplier else "N/A"}',
                                created_by=request.user
                            )

                            print(f"✅ Imported {received_qty} {po_item.product.name} from PO {po.po_code}")

                        except ValueError as ve:
                            print(f"❌ Inventory import error: {ve}")
                            raise ValueError(str(ve))

                # Update PO status
                all_received = all(
                    item.received_quantity >= item.quantity
                    for item in po.items.all()
                )

                if all_received:
                    po.status = 'received'
                    po.received_date = timezone.now().date()
                else:
                    po.status = 'partial'  # Partial receive

                po.updated_by = request.user
                po.save()

            serializer = PurchaseOrderDetailSerializer(po)

            return Response({
                'status': '1',
                'response': {
                    'message': 'Nhận hàng thành công',
                    'purchase_order': serializer.data
                }
            }, status=status.HTTP_200_OK)

        except Exception as ex:
            return Response({
                'status': '2',
                'response': {
                    'error_code': '9999',
                    'error_message_us': 'System error',
                    'error_message_vn': f'Lỗi hệ thống: {str(ex)}'
                }
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)






