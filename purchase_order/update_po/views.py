from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from django.db import transaction
from django.utils import timezone
from core.models import PurchaseOrder
from purchase_order.serializers import PurchaseOrderDetailSerializer


class UpdatePurchaseOrderStatusView(APIView):
    permission_classes = [IsAuthenticated]

    def put(self, request, po_id):
        try:
            new_status = request.data.get('status')

            if new_status not in ['draft', 'pending', 'approved', 'cancelled']:
                return Response({
                    'status': '2',
                    'response': {
                        'error_code': '001',
                        'error_message_us': 'Invalid status',
                        'error_message_vn': 'Trạng thái không hợp lệ'
                    }
                }, status=status.HTTP_400_BAD_REQUEST)

            try:
                po = PurchaseOrder.objects.get(id=po_id, is_active=True)
            except PurchaseOrder.DoesNotExist:
                return Response({
                    'status': '2',
                    'response': {
                        'error_code': '002',
                        'error_message_us': 'Purchase order not found',
                        'error_message_vn': 'Không tìm thấy đơn đặt hàng'
                    }
                }, status=status.HTTP_404_NOT_FOUND)

            with transaction.atomic():
                po.status = new_status
                po.updated_by = request.user

                if new_status == 'approved':
                    po.approved_by = request.user
                    po.approved_at = timezone.now()

                po.save()

            serializer = PurchaseOrderDetailSerializer(po)

            return Response({
                'status': '1',
                'response': {
                    'message': 'Cập nhật trạng thái thành công',
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


class DeletePurchaseOrderView(APIView):
    permission_classes = [IsAuthenticated]

    def delete(self, request, po_id):
        try:
            po = PurchaseOrder.objects.get(id=po_id, is_active=True)

            # Only allow deleting draft or cancelled POs
            if po.status not in ['draft', 'cancelled']:
                return Response({
                    'status': '2',
                    'response': {
                        'error_code': '003',
                        'error_message_us': 'Cannot delete approved/received PO',
                        'error_message_vn': 'Không thể xóa đơn đã duyệt/đã nhận'
                    }
                }, status=status.HTTP_400_BAD_REQUEST)

            po.is_active = False
            po.updated_by = request.user
            po.save()

            return Response({
                'status': '1',
                'response': {
                    'message': 'Xóa đơn đặt hàng thành công'
                }
            }, status=status.HTTP_200_OK)

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

