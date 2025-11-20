from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from core.models import PurchaseOrder
from purchase_order.email_service import PurchaseOrderEmailService


class SendPurchaseOrderEmailView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, po_id):
        """Manually send or resend purchase order email to supplier"""
        try:
            po = PurchaseOrder.objects.prefetch_related('items__product').get(
                id=po_id, is_active=True
            )

            # Check if supplier has email
            if not po.supplier.email:
                return Response({
                    'status': '2',
                    'response': {
                        'error_code': '003',
                        'error_message_us': 'Supplier has no email',
                        'error_message_vn': 'Nhà cung cấp chưa có email'
                    }
                }, status=status.HTTP_400_BAD_REQUEST)

            # Send email
            email_sent = PurchaseOrderEmailService.send_purchase_order_email(po)

            if email_sent:
                return Response({
                    'status': '1',
                    'response': {
                        'message': f'Đã gửi email thành công đến {po.supplier.email}',
                        'supplier_email': po.supplier.email
                    }
                }, status=status.HTTP_200_OK)
            else:
                return Response({
                    'status': '2',
                    'response': {
                        'error_code': '004',
                        'error_message_us': 'Failed to send email',
                        'error_message_vn': 'Gửi email thất bại. Vui lòng thử lại sau.'
                    }
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        except PurchaseOrder.DoesNotExist:
            return Response({
                'status': '2',
                'response': {
                    'error_code': '002',
                    'error_message_us': 'Purchase order not found',
                    'error_message_vn': 'Không tìm thấy đơn đặt hàng'
                }
            }, status=status.HTTP_404_NOT_FOUND)

        except Exception as ex:
            return Response({
                'status': '2',
                'response': {
                    'error_code': '9999',
                    'error_message_us': 'System error',
                    'error_message_vn': f'Lỗi hệ thống: {str(ex)}'
                }
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)






