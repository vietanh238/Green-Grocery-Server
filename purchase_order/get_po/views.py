from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from django.db.models import Q
from core.models import PurchaseOrder
from purchase_order.serializers import PurchaseOrderListSerializer, PurchaseOrderDetailSerializer


class GetPurchaseOrdersView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            search_query = request.GET.get('search', '').strip()
            po_status = request.GET.get('status', '').strip()
            supplier_id = request.GET.get('supplier_id', '').strip()

            purchase_orders = PurchaseOrder.objects.select_related(
                'supplier', 'created_by', 'approved_by'
            ).prefetch_related('items__product').filter(is_active=True)

            if search_query:
                purchase_orders = purchase_orders.filter(
                    Q(po_code__icontains=search_query) |
                    Q(supplier__name__icontains=search_query) |
                    Q(supplier__supplier_code__icontains=search_query)
                )

            if po_status:
                purchase_orders = purchase_orders.filter(status=po_status)

            if supplier_id:
                purchase_orders = purchase_orders.filter(supplier_id=supplier_id)

            purchase_orders = purchase_orders.order_by('-created_at')

            serializer = PurchaseOrderListSerializer(purchase_orders, many=True)

            # Calculate stats
            stats = {
                'total_count': purchase_orders.count(),
                'draft_count': purchase_orders.filter(status='draft').count(),
                'pending_count': purchase_orders.filter(status='pending').count(),
                'approved_count': purchase_orders.filter(status='approved').count(),
                'received_count': purchase_orders.filter(status='received').count(),
                'cancelled_count': purchase_orders.filter(status='cancelled').count(),
            }

            return Response({
                'status': '1',
                'response': {
                    'data': serializer.data,
                    'stats': stats
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


class GetPurchaseOrderDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, po_id):
        try:
            po = PurchaseOrder.objects.select_related(
                'supplier', 'created_by', 'approved_by'
            ).prefetch_related('items__product').get(id=po_id, is_active=True)

            serializer = PurchaseOrderDetailSerializer(po)

            return Response({
                'status': '1',
                'response': serializer.data
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




