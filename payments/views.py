from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.db import transaction
from django.utils import timezone
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from decouple import config

from core.models import Payment, Order, OrderItem, Product
from .utils import verify_checksum

CHECKSUM_KEY = config("PAYOS_CHECKSUM_KEY")


class WebhookView(APIView):

    def get(self, request):
        return Response({
            "message": "Webhook URL is verified."
        }, status=status.HTTP_200_OK)

    def post(self, request):
        try:
            payload = request.data
            signature = payload.get('signature')
            data_from_payload = payload.get("data", {})

            if not data_from_payload or not isinstance(data_from_payload, dict):
                return Response({
                    "status": "ok",
                    "message": "Webhook URL verified successfully"
                }, status=status.HTTP_200_OK)

            data_from_payload['signature'] = signature

            try:
                is_valid = verify_checksum(
                    data_from_payload,
                    CHECKSUM_KEY,
                    checksum_field="signature"
                )
            except Exception as e:
                print(f"Lỗi xác thực checksum: {e}")
                is_valid = False

            if not is_valid:
                return Response({
                    "error": "Invalid checksum"
                }, status=status.HTTP_400_BAD_REQUEST)

            order_code = str(data_from_payload.get("orderCode", ""))
            transaction_id = data_from_payload.get("paymentLinkId")
            payment_status_code = payload.get("code")

            with transaction.atomic():
                try:
                    payment = Payment.objects.select_related('order').get(
                        order_code=order_code
                    )
                except Payment.DoesNotExist:
                    return Response({
                        "error": "Order not found"
                    }, status=status.HTTP_404_NOT_FOUND)

                if payment.status == 'paid':
                    return Response({
                        "status": "ok",
                        "message": "Payment already processed"
                    }, status=status.HTTP_200_OK)

                if payment_status_code == "00":
                    payment.status = 'paid'
                    payment.paid_at = timezone.now()
                    payment.paid_amount = payment.amount

                    if payment.order:
                        payment.order.status = 'paid'
                        payment.order.paid_amount = payment.amount
                        payment.order.completed_at = timezone.now()
                        payment.order.save()

                    list_product_reorder = []
                    order_items = payment.order.items.all() if payment.order else []

                    for order_item in order_items:
                        if order_item.product:
                            product = order_item.product

                            old_quantity = product.stock_quantity
                            product.stock_quantity = max(
                                0, product.stock_quantity - order_item.quantity)
                            product.total_sold += order_item.quantity
                            product.total_revenue += float(
                                order_item.total_price)
                            product.last_sold_date = timezone.now()
                            product.save()

                            if product.stock_quantity <= product.reorder_point:
                                list_product_reorder.append({
                                    'bar_code': product.bar_code,
                                    'name': product.name,
                                    'stock_quantity': product.stock_quantity,
                                    'reorder_point': product.reorder_point
                                })

                else:
                    payment.status = 'failed'
                    payment.failed_at = timezone.now()

                    if payment.order:
                        payment.order.status = 'failed'
                        payment.order.save()

                if transaction_id:
                    payment.transaction_id = transaction_id

                payment.save()

                if payment.status == 'paid':
                    channel_layer = get_channel_layer()

                    async_to_sync(channel_layer.group_send)(
                        "broadcast",
                        {
                            "type": "payment_success",
                            "data": {
                                "message_type": "payment_success",
                                "orderCode": payment.order_code,
                                "amount": float(payment.amount),
                                "message": "Thanh toán thành công"
                            }
                        }
                    )

                    if list_product_reorder:
                        async_to_sync(channel_layer.group_send)(
                            "broadcast",
                            {
                                "type": "message",
                                "data": {
                                    'message_type': 'remind_reorder',
                                    "items": list_product_reorder,
                                    "message": "Có sản phẩm sắp hết hàng"
                                }
                            }
                        )

                return Response({
                    "status": "ok",
                    "message": "Webhook processed successfully"
                }, status=status.HTTP_200_OK)

        except Exception as ex:
            print(f"Webhook error: {str(ex)}")
            return Response({
                "error": f"Internal server error: {str(ex)}"
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
