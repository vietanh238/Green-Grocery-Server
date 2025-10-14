from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.db import transaction
import os
import json
from decouple import config
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from product.models import Product
from .models import Payment
from .services import create_payment_request, delete_payment
from .utils import verify_checksum

CHECKSUM_KEY = config("PAYOS_CHECKSUM_KEY", "your_checksum_key")


class CreatePaymentView(APIView):

    def post(self, request):
        payload = request.data

        required_fields = ["orderCode", "amount",
                           "description", "returnUrl", "cancelUrl"]
        missing = [f for f in required_fields if f not in payload]
        if missing:
            return Response(
                {"error": f"Missing fields: {', '.join(missing)}"},
                status=status.HTTP_400_BAD_REQUEST
            )

        order_code = payload["orderCode"]
        amount = int(payload["amount"])
        description = payload.get("description", "")
        return_url = payload["returnUrl"]
        cancel_url = payload["cancelUrl"]
        items = payload.get("items")

        with transaction.atomic():
            payment, created = Payment.objects.get_or_create(
                order_code=order_code,
                defaults={
                    "amount": amount,
                    "description": description
                }
            )
            if not created and payment.status == "paid":
                return Response(
                    {
                        "error": "Order already paid",
                        "orderCode": order_code,
                        "status": payment.status
                    },
                    status=status.HTTP_400_BAD_REQUEST
                )

            try:
                payos_res = create_payment_request(
                    order_code=order_code,
                    amount=amount,
                    description=description,
                    return_url=return_url,
                    cancel_url=cancel_url
                )
            except Exception as e:
                return Response(
                    {"error": f"PayOS error: {str(e)}"},
                    status=status.HTTP_502_BAD_GATEWAY
                )
            data = payos_res.get("data", {})
            transaction_id = data.get("paymentLinkId")
            checkout_url = data.get("checkoutUrl")
            qr_code = data.get("qrCode")

            payment.transaction_id = transaction_id
            payment.status = "pending"

            # update stock quantity product
            items = json.dumps(items)
            payment.items = items
            payment.save()

            return Response({
                'status': '1',
                'response': {
                    "orderCode": order_code,
                    "amount": amount,
                    "transactionId": transaction_id,
                    "checkoutUrl": checkout_url,
                    "qrCode": qr_code
                }
            })

    def delete(self, request, pk):
        order_code = pk
        if not order_code:
            return
        with transaction.atomic():
            try:
                payment_delete = Payment.objects.get(order_code=order_code)
                payos_res = delete_payment(order_code)
                if payos_res['code'] == '00':
                    payment_delete.status = "delete"
                payment_delete.save()
                return Response({
                    'status': '1',
                    'response': {
                        "order_code": order_code
                    }
                })
            except Exception as ex:
                return Response({
                    'status': '2',
                    'response': {
                        "error_code": "9999",
                        "error_message_us": "System error",
                        "error_message_vn": "Lỗi hệ thống"
                    }
                })


class WebhookView(APIView):

    def get(self, request):
        return Response({"message": "Webhook URL is verified."}, status=status.HTTP_200_OK)

    def post(self, request):
        payload = request.data
        signature = payload['signature']
        data_from_payload = payload.get("data")
        data_from_payload['signature'] = signature
        list_product_reorder = []

        if not data_from_payload or not isinstance(data_from_payload, dict):
            return Response({"status": "ok", "message": "Webhook URL verified successfully"}, status=status.HTTP_200_OK)

        try:
            is_valid = verify_checksum(
                data_from_payload, CHECKSUM_KEY, checksum_field="signature")
        except Exception as e:
            print(f"Lỗi khi xác thực checksum: {e}")
            is_valid = False

        if not is_valid:
            return Response({"error": "Invalid checksum"}, status=status.HTTP_400_BAD_REQUEST)

        order_code = data_from_payload.get("orderCode")
        transaction_id = data_from_payload.get("paymentLinkId")

        try:
            payment = Payment.objects.get(order_code=order_code)
        except Payment.DoesNotExist:
            return Response({"error": "Order not found"}, status=status.HTTP_404_NOT_FOUND)

        payment_status_code = payload.get("code")
        if payment_status_code == "00":
            payment.status = "paid"
            items = json.loads(payment.items)
            for item in items:
                product = Product.objects.filter(bar_code=item.get('bar_code')).first()
                if product:
                    product.stock_quantity = product.stock_quantity - item.get('quantity')
                    if product.stock_quantity <= product.reorder_point:
                        list_product_reorder.append(product.bar_code)
            product.save()
        else:
            payment.status = "failed"

        if transaction_id:
            payment.transaction_id = transaction_id

        payment.save()
        if payment.status == "paid":
            user_id = getattr(payment, "user_id", None)
            amount = getattr(payment, "amount", None)

            if user_id:
                notify_payment_success(
                    user_id=user_id, order_id=payment.order_code, amount=amount)
                if list_product_reorder:
                    channel_layer = get_channel_layer()
                    async_to_sync(channel_layer.group_send)(
                        "broadcast",
                        {
                            "type": "remind_reorder",
                            "data": {
                                "items": list_product_reorder,
                                "message": "Sản phẩm gần sắp hết"
                            }
                        }
                    )
            else:
                channel_layer = get_channel_layer()
                async_to_sync(channel_layer.group_send)(
                    "broadcast",
                    {
                        "type": "payment_success",
                        "data": {
                            "orderId": payment.order_code,
                            "amount": amount,
                            "message": "Thanh toán thành công (broadcast)"
                        }
                    }
                )
                if list_product_reorder:
                    channel_layer = get_channel_layer()
                    async_to_sync(channel_layer.group_send)(
                        "broadcast",
                        {
                            "type": "message",
                            "data": {
                                'message_type': 'remind_reorder',
                                "items": list_product_reorder,
                                "message": "Sản phẩm gần sắp hết"
                            }
                        }
                    )
        return Response({"status": "ok"}, status=status.HTTP_200_OK)


def notify_payment_success(user_id: int, order_id: int, amount: int):
    channel_layer = get_channel_layer()
    data = {
        "orderId": order_id,
        "amount": amount,
        "message": "Thanh toán thành công",
    }
    async_to_sync(channel_layer.group_send)(
        f"user_{user_id}",
        {
            "type": "payment_success",
            "data": data,
        }
    )
