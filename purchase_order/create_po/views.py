from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from django.db import transaction
from django.utils import timezone
from core.models import PurchaseOrder, PurchaseOrderItem, Product, Supplier
from purchase_order.serializers import CreatePurchaseOrderSerializer, PurchaseOrderDetailSerializer
from purchase_order.email_service import PurchaseOrderEmailService


class CreatePurchaseOrderView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        try:
            serializer = CreatePurchaseOrderSerializer(data=request.data)

            if not serializer.is_valid():
                return Response({
                    'status': '2',
                    'response': {
                        'error_code': '001',
                        'error_message_us': 'Validation error',
                        'error_message_vn': 'Dữ liệu không hợp lệ',
                        'errors': serializer.errors
                    }
                }, status=status.HTTP_400_BAD_REQUEST)

            data = serializer.validated_data

            try:
                supplier = Supplier.objects.get(id=data['supplier_id'], is_active=True)
            except Supplier.DoesNotExist:
                return Response({
                    'status': '2',
                    'response': {
                        'error_code': '002',
                        'error_message_us': 'Supplier not found',
                        'error_message_vn': 'Không tìm thấy nhà cung cấp'
                    }
                }, status=status.HTTP_404_NOT_FOUND)

            with transaction.atomic():
                # Generate PO code
                import random
                import string
                po_code = f"PO{timezone.now().strftime('%Y%m%d')}{''.join(random.choices(string.digits, k=4))}"

                # Calculate total
                total_amount = sum(item['total_price'] for item in data['items'])

                # Create Purchase Order
                po = PurchaseOrder.objects.create(
                    po_code=po_code,
                    supplier=supplier,
                    status='draft',
                    total_amount=total_amount,
                    expected_date=data['expected_date'],
                    note=data.get('note', ''),
                    created_by=request.user,
                    updated_by=request.user
                )

                # Create PO Items
                for item_data in data['items']:
                    try:
                        product = Product.objects.get(id=item_data['product_id'], is_active=True)
                    except Product.DoesNotExist:
                        continue

                    PurchaseOrderItem.objects.create(
                        purchase_order=po,
                        product=product,
                        quantity=item_data['quantity'],
                        unit_price=item_data['unit_price'],
                        total_price=item_data['total_price'],
                        note=item_data.get('note', '')
                    )

                po_data = PurchaseOrderDetailSerializer(po).data

                # Send email to supplier
                email_sent = False
                try:
                    email_sent = PurchaseOrderEmailService.send_purchase_order_email(po)
                except:
                    pass  # Don't fail if email fails

                return Response({
                    'status': '1',
                    'response': {
                        'message': 'Tạo đơn đặt hàng thành công' + (' và đã gửi email cho nhà cung cấp' if email_sent else ''),
                        'purchase_order': po_data,
                        'email_sent': email_sent
                    }
                }, status=status.HTTP_201_CREATED)

        except Exception as ex:
            return Response({
                'status': '2',
                'response': {
                    'error_code': '9999',
                    'error_message_us': 'System error',
                    'error_message_vn': f'Lỗi hệ thống: {str(ex)}'
                }
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

