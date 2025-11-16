
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.db import transaction
import json
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from core.models import Product, Category
from core.models import Payment
import time


class CashPaymentView(APIView):

    def post(self, request):
        payload = request.data

        required_fields = ["amount", "items"]
        missing = [f for f in required_fields if f not in payload]
        if missing:
            return Response(
                {"error": f"Missing fields: {', '.join(missing)}"},
                status=status.HTTP_400_BAD_REQUEST
            )

        amount = int(payload["amount"])
        items = payload.get("items", [])
        payment_method = payload.get("payment_method", "cash")

        with transaction.atomic():
            order_code = f"CASH{int(time.time() * 1000)}"

            payment = Payment.objects.create(
                order_code=order_code,
                amount=amount,
                description=f"Thanh toán tiền mặt - {order_code}",
                status="paid",
                items=json.dumps(items),
                transaction_id=order_code
            )

            list_product_reorder = []

            for item in items:
                bar_code = item.get('bar_code') or item.get('sku')
                quantity = item.get('quantity', 0)

                if bar_code:
                    try:
                        product = Product.objects.get(bar_code=bar_code)
                        product.stock_quantity = max(
                            0, product.stock_quantity - quantity)

                        if product.stock_quantity <= product.reorder_point:
                            list_product_reorder.append(product.bar_code)

                        product.save()
                    except Product.DoesNotExist:
                        pass

            channel_layer = get_channel_layer()
            async_to_sync(channel_layer.group_send)(
                "broadcast",
                {
                    "type": "payment_success",
                    "data": {
                        "orderCode": payment.order_code,
                        "amount": amount,
                        "paymentMethod": payment_method,
                        "message": "Thanh toán tiền mặt thành công"
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
                            "message": "Sản phẩm gần sắp hết"
                        }
                    }
                )

            return Response({
                'status': '1',
                'response': {
                    "orderCode": order_code,
                    "amount": amount,
                    "status": "paid",
                    "paymentMethod": payment_method,
                    "message": "Thanh toán thành công"
                }
            }, status=status.HTTP_200_OK)
