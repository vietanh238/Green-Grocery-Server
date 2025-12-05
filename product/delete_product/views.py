from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from django.db import transaction
from core.models import Product, InventoryTransaction, PurchaseOrderItem


class DeleteProductView(APIView):
    permission_classes = [IsAuthenticated]

    def delete(self, request, bar_code):
        try:
            user = request.user

            try:
                product = Product.objects.get(
                    bar_code=bar_code, is_active=True, created_by=user)
            except Product.DoesNotExist:
                return Response({
                    'status': '2',
                    'response': {
                        'error_code': '005',
                        'error_message_us': 'Product not found',
                        'error_message_vn': 'Không tìm thấy sản phẩm'
                    }
                }, status=status.HTTP_404_NOT_FOUND)

            with transaction.atomic():
                inventory_transactions = InventoryTransaction.objects.filter(product=product)
                purchase_order_items = PurchaseOrderItem.objects.filter(product=product)

                active_purchase_orders = purchase_order_items.filter(
                    purchase_order__status__in=['draft', 'pending', 'approved']
                )

                if active_purchase_orders.exists():
                    return Response({
                        'status': '2',
                        'response': {
                            'error_code': '006',
                            'error_message_us': 'Product is in active purchase orders',
                            'error_message_vn': 'Không thể xóa sản phẩm vì đang có trong đơn nhập hàng chưa hoàn thành. Vui lòng hoàn thành hoặc hủy đơn nhập hàng trước.'
                        }
                    }, status=status.HTTP_400_BAD_REQUEST)

                inventory_transactions.delete()
                purchase_order_items.delete()

                product.is_active = False
                product.updated_by = user
                product.save()
                product.delete()

            return Response({
                'status': '1',
                'response': {
                    'message': 'Xóa sản phẩm thành công'
                }
            }, status=status.HTTP_200_OK)

        except Exception as ex:
            return Response({
                'status': '2',
                'response': {
                    'error_code': '9999',
                    'error_message_us': 'An internal server error occurred.',
                    'error_message_vn': f'Lỗi hệ thống: {str(ex)}'
                }
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
