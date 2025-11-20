from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from django.db import transaction
from django.utils import timezone
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from decimal import Decimal
import time

from core.models import Payment, Order, OrderItem, Product
from core.services.inventory_service import InventoryService
from .serializers import CashPaymentSerializer


class CashPaymentView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        try:
            serializer = CashPaymentSerializer(data=request.data)

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
            amount = data['amount']
            items_data = data['items']
            payment_method = data.get('payment_method', 'cash')
            note = data.get('note', '')

            with transaction.atomic():
                order_code = f"CASH{int(time.time() * 1000)}"

                subtotal = sum(item['total_price'] for item in items_data)

                order = Order.objects.create(
                    order_code=order_code,
                    user=request.user if request.user.is_authenticated else None,
                    status='paid',
                    subtotal=subtotal,
                    total_amount=amount,
                    paid_amount=amount,
                    payment_method=payment_method,
                    note=note,
                    completed_at=timezone.now(),
                    created_by=request.user if request.user.is_authenticated else None,
                    updated_by=request.user if request.user.is_authenticated else None
                )

                order_items = []
                list_product_reorder = []

                for item_data in items_data:
                    try:
                        product = Product.objects.get(
                            bar_code=item_data['bar_code'],
                            is_active=True
                        )

                        # ✅ Use InventoryService để track xuất kho
                        try:
                            inventory_result = InventoryService.export_stock(
                                product_id=product.id,
                                quantity=item_data['quantity'],
                                unit_price=item_data['unit_price'],
                                reference_type='order',
                                reference_id=None,  # Will update after order saved
                                note=f"Bán hàng - Order: {order_code}",
                                created_by=request.user if request.user.is_authenticated else None
                            )

                            # Get updated product from inventory service
                            product = inventory_result['product']

                        except ValueError as ve:
                            raise ValueError(str(ve))

                        order_item = OrderItem(
                            order=order,
                            product=product,
                            product_name=item_data['name'],
                            product_sku=item_data['sku'],
                            quantity=item_data['quantity'],
                            unit_price=item_data['unit_price'],
                            total_price=item_data['total_price'],
                            cost_price=product.cost_price,
                            created_by=request.user if request.user.is_authenticated else None,
                            updated_by=request.user if request.user.is_authenticated else None
                        )
                        order_items.append(order_item)

                        # Update product sales stats
                        product.total_sold += int(item_data['quantity'])
                        product.total_revenue += Decimal(str(item_data['total_price']))
                        product.save()

                        # Check reorder point
                        if product.stock_quantity <= product.reorder_point:
                            list_product_reorder.append({
                                'bar_code': product.bar_code,
                                'name': product.name,
                                'stock_quantity': product.stock_quantity,
                                'reorder_point': product.reorder_point
                            })

                    except Product.DoesNotExist:
                        # Product not found - create order item without inventory tracking
                        order_item = OrderItem(
                            order=order,
                            product=None,
                            product_name=item_data['name'],
                            product_sku=item_data['sku'],
                            quantity=item_data['quantity'],
                            unit_price=item_data['unit_price'],
                            total_price=item_data['total_price'],
                            cost_price=0,
                            created_by=request.user if request.user.is_authenticated else None,
                            updated_by=request.user if request.user.is_authenticated else None
                        )
                        order_items.append(order_item)

                OrderItem.objects.bulk_create(order_items)

                payment = Payment.objects.create(
                    order=order,
                    order_code=order_code,
                    transaction_id=order_code,
                    payment_method=payment_method,
                    amount=amount,
                    paid_amount=amount,
                    status='paid',
                    description=f"Thanh toán {payment_method} - {order_code}",
                    paid_at=timezone.now(),
                    created_by=request.user if request.user.is_authenticated else None,
                    updated_by=request.user if request.user.is_authenticated else None
                )

                # WebSocket notifications (optional - requires Redis)
                try:
                    channel_layer = get_channel_layer()
                    print(f"🔌 Channel layer: {channel_layer}")

                    if channel_layer:
                        # Send payment success notification
                        async_to_sync(channel_layer.group_send)(
                            "broadcast",
                            {
                                "type": "payment_success",
                                "data": {
                                    "message_type": "payment_success",
                                    "order_code": order_code,
                                    "orderCode": order_code,
                                    "amount": float(amount),
                                    "payment_method": payment_method,
                                    "paymentMethod": payment_method,
                                    "message": f"Thanh toán {payment_method} thành công"
                                }
                            }
                        )
                        print(f"✅ Payment success notification sent: {order_code}")

                        # Send low stock notification
                        if list_product_reorder:
                            print(f"🔔 Sending low stock alert for {len(list_product_reorder)} products")
                            async_to_sync(channel_layer.group_send)(
                                "broadcast",
                                {
                                    "type": "remind_reorder",
                                    "data": {
                                        'message_type': 'remind_reorder',
                                        "items": list_product_reorder,
                                        "count": len(list_product_reorder),
                                        "message": f"Có {len(list_product_reorder)} sản phẩm sắp hết hàng"
                                    }
                                }
                            )
                            print(f"✅ Low stock notification sent: {list_product_reorder}")
                        else:
                            print("ℹ️ No products need reorder alert")
                    else:
                        print("⚠️ Channel layer is None - WebSocket not configured or Redis not running")
                except Exception as ws_error:
                    # WebSocket failed but payment still successful
                    print(f"❌ WebSocket notification failed: {ws_error}")
                    import traceback
                    traceback.print_exc()

                return Response({
                    'status': '1',
                    'response': {
                        "order_code": order_code,
                        "orderCode": order_code,  # Keep for backward compatibility
                        "amount": float(amount),
                        "status": "paid",
                        "payment_method": payment_method,
                        "paymentMethod": payment_method,  # Keep for backward compatibility
                        "message": "Thanh toán thành công"
                    }
                }, status=status.HTTP_200_OK)

        except ValueError as ve:
            return Response({
                'status': '2',
                'response': {
                    'error_code': '002',
                    'error_message_us': str(ve),
                    'error_message_vn': str(ve)
                }
            }, status=status.HTTP_400_BAD_REQUEST)
        except Exception as ex:
            return Response({
                'status': '2',
                'response': {
                    'error_code': '9999',
                    'error_message_us': 'An internal server error occurred.',
                    'error_message_vn': f'Lỗi hệ thống: {str(ex)}'
                }
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
