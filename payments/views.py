from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.db import transaction
import os
import json
from decouple import config


from .models import Payment
from .services import create_payment_request
from .utils import verify_checksum

CHECKSUM_KEY = config("PAYOS_CHECKSUM_KEY", "your_checksum_key")


class CreatePaymentView(APIView):

    def post(self, request):
        payload = request.data

        required_fields = ["orderCode", "amount", "description", "returnUrl", "cancelUrl"]
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
                    cancel_url=cancel_url,
                    buyer=buyer
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


class WebhookView(APIView):

    def post(self, request):
        payload = request.data
        try:
            is_valid = verify_checksum(payload, CHECKSUM_KEY, checksum_field="checksum")
        except Exception:
            is_valid = False

        if not is_valid:
            return Response({"error": "Invalid checksum"}, status=status.HTTP_400_BAD_REQUEST)

        order_code = payload.get("orderCode")
        status_str = payload.get("status")
        transaction_id = payload.get("transactionId")

        if not order_code:
            return Response({"error": "Missing orderCode"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            payment = Payment.objects.get(order_code=order_code)
        except Payment.DoesNotExist:
            return Response({"error": "Order not found"}, status=status.HTTP_404_NOT_FOUND)

        if status_str == "PAID":
            payment.status = "paid"
        elif status_str == "CANCELED":
            payment.status = "canceled"
        elif status_str == "FAILED":
            payment.status = "failed"
        else:
            payment.status = "unknown"

        if transaction_id:
            payment.transaction_id = transaction_id

        payment.save()

        return Response({"status": "ok"}, status=status.HTTP_200_OK)
