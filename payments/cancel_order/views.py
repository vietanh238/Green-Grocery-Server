from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from django.db import transaction
from django.utils import timezone
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync

from core.models import Order, Payment, OrderItem
from core.services.inventory_service import InventoryService


class CancelOrderView(APIView):
    """Cancel an order and return stock"""
    permission_classes = [IsAuthenticated]

    def post(self, request, order_code):
        try:
            # Get order
            try:
                order = Order.objects.prefetch_related('items__product').get(
                    order_code=order_code,
                    created_by=request.user
                )
            except Order.DoesNotExist:
                return Response({
                    'status': '2',
                    'response': {
                        'error_code': '404',
                        'error_message_vn': 'Không tìm thấy đơn hàng'
                    }
                }, status=status.HTTP_404_NOT_FOUND)

            # Check if order can be cancelled
            if order.status == 'cancelled':
                return Response({
                    'status': '2',
                    'response': {
                        'error_code': '001',
                        'error_message_vn': 'Đơn hàng đã được hủy trước đó'
                    }
                }, status=status.HTTP_400_BAD_REQUEST)

            if order.status == 'refunded':
                return Response({
                    'status': '2',
                    'response': {
                        'error_code': '002',
                        'error_message_vn': 'Đơn hàng đã được hoàn tiền, không thể hủy'
                    }
                }, status=status.HTTP_400_BAD_REQUEST)

            cancel_reason = request.data.get('reason', 'Hủy đơn hàng')

            with transaction.atomic():
                # Return stock for all items
                returned_items = []
                for order_item in order.items.all():
                    if order_item.product:
                        try:
                            # Return stock using InventoryService
                            inventory_result = InventoryService.return_stock(
                                product_id=order_item.product.id,
                                quantity=order_item.quantity,
                                unit_price=order_item.unit_price,
                                reference_type='order_cancel',
                                reference_id=order.id,
                                note=f'Hoàn hàng - Hủy đơn {order_code}: {cancel_reason}',
                                created_by=request.user
                            )

                            # Update product sales stats (reduce)
                            product = order_item.product
                            product.total_sold = max(0, product.total_sold - order_item.quantity)
                            product.total_revenue = max(0, product.total_revenue - order_item.total_price)
                            product.save()

                            returned_items.append({
                                'product_name': product.name,
                                'quantity': order_item.quantity,
                                'returned': True
                            })

                        except Exception as e:
                            print(f"Error returning stock: {e}")
                            returned_items.append({
                                'product_name': order_item.product.name,
                                'quantity': order_item.quantity,
                                'returned': False,
                                'error': str(e)
                            })

                # Update order status
                order.status = 'cancelled'
                order.cancelled_at = timezone.now()
                order.note = f"{order.note or ''}\n[Cancelled] {cancel_reason}".strip()
                order.updated_by = request.user
                order.save()

                # Update payment if exists
                try:
                    payment = Payment.objects.get(order_code=order_code)
                    if payment.status == 'paid':
                        payment.status = 'cancelled'
                        payment.save()
                except Payment.DoesNotExist:
                    pass

                # Send WebSocket notification
                try:
                    channel_layer = get_channel_layer()
                    if channel_layer:
                        async_to_sync(channel_layer.group_send)(
                            "broadcast",
                            {
                                "type": "message",
                                "data": {
                                    'message_type': 'order_cancelled',
                                    "order_code": order_code,
                                    "message": f"Đơn hàng {order_code} đã được hủy"
                                }
                            }
                        )
                except Exception as ws_error:
                    print(f"WebSocket error: {ws_error}")

            return Response({
                'status': '1',
                'response': {
                    'message': 'Hủy đơn hàng thành công',
                    'order_code': order_code,
                    'returned_items': returned_items,
                    'cancelled_at': order.cancelled_at.isoformat()
                }
            }, status=status.HTTP_200_OK)

        except Exception as ex:
            return Response({
                'status': '2',
                'response': {
                    'error_code': '9999',
                    'error_message_vn': f'Lỗi hệ thống: {str(ex)}'
                }
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class RefundOrderView(APIView):
    """Refund an order (full or partial)"""
    permission_classes = [IsAuthenticated]

    def post(self, request, order_code):
        try:
            # Get order
            try:
                order = Order.objects.prefetch_related('items__product').get(
                    order_code=order_code,
                    created_by=request.user
                )
            except Order.DoesNotExist:
                return Response({
                    'status': '2',
                    'response': {
                        'error_code': '404',
                        'error_message_vn': 'Không tìm thấy đơn hàng'
                    }
                }, status=status.HTTP_404_NOT_FOUND)

            # Check if order can be refunded
            if order.status not in ['paid', 'cancelled']:
                return Response({
                    'status': '2',
                    'response': {
                        'error_code': '001',
                        'error_message_vn': 'Chỉ có thể hoàn tiền đơn hàng đã thanh toán'
                    }
                }, status=status.HTTP_400_BAD_REQUEST)

            if order.status == 'refunded':
                return Response({
                    'status': '2',
                    'response': {
                        'error_code': '002',
                        'error_message_vn': 'Đơn hàng đã được hoàn tiền'
                    }
                }, status=status.HTTP_400_BAD_REQUEST)

            refund_amount = request.data.get('refund_amount', order.total_amount)
            refund_reason = request.data.get('reason', 'Hoàn tiền')
            refund_items = request.data.get('items', [])  # For partial refund

            try:
                refund_amount = float(refund_amount)
                if refund_amount <= 0 or refund_amount > float(order.total_amount):
                    raise ValueError()
            except:
                return Response({
                    'status': '2',
                    'response': {
                        'error_code': '003',
                        'error_message_vn': 'Số tiền hoàn không hợp lệ'
                    }
                }, status=status.HTTP_400_BAD_REQUEST)

            with transaction.atomic():
                # Handle item returns if specified
                returned_items = []
                if refund_items:
                    for refund_item in refund_items:
                        item_id = refund_item.get('item_id')
                        refund_quantity = refund_item.get('quantity', 0)

                        try:
                            order_item = order.items.get(id=item_id)
                            if order_item.product and refund_quantity > 0:
                                # Return stock
                                inventory_result = InventoryService.return_stock(
                                    product_id=order_item.product.id,
                                    quantity=refund_quantity,
                                    unit_price=order_item.unit_price,
                                    reference_type='order_refund',
                                    reference_id=order.id,
                                    note=f'Hoàn hàng - Refund {order_code}: {refund_reason}',
                                    created_by=request.user
                                )

                                returned_items.append({
                                    'product_name': order_item.product.name,
                                    'quantity': refund_quantity,
                                    'returned': True
                                })
                        except Exception as e:
                            print(f"Error returning item: {e}")

                # Update order status
                order.status = 'refunded'
                order.note = f"{order.note or ''}\n[Refunded] {refund_amount}đ - {refund_reason}".strip()
                order.updated_by = request.user
                order.save()

                # Update payment
                try:
                    payment = Payment.objects.get(order_code=order_code)
                    payment.status = 'refunded'
                    payment.save()
                except Payment.DoesNotExist:
                    pass

                # Send WebSocket notification
                try:
                    channel_layer = get_channel_layer()
                    if channel_layer:
                        async_to_sync(channel_layer.group_send)(
                            "broadcast",
                            {
                                "type": "message",
                                "data": {
                                    'message_type': 'order_refunded',
                                    "order_code": order_code,
                                    "refund_amount": refund_amount,
                                    "message": f"Đơn hàng {order_code} đã được hoàn tiền"
                                }
                            }
                        )
                except Exception as ws_error:
                    print(f"WebSocket error: {ws_error}")

            return Response({
                'status': '1',
                'response': {
                    'message': 'Hoàn tiền thành công',
                    'order_code': order_code,
                    'refund_amount': refund_amount,
                    'returned_items': returned_items
                }
            }, status=status.HTTP_200_OK)

        except Exception as ex:
            return Response({
                'status': '2',
                'response': {
                    'error_code': '9999',
                    'error_message_vn': f'Lỗi hệ thống: {str(ex)}'
                }
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

