from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from django.db.models import Q
from django.contrib.auth.models import User
import json
from core.models import Product, Payment
from core.models import Customer

class GetUserProfile(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            user = request.user

            return Response({
                "status": "1",
                "response": {
                    "id": user.id,
                    "username": user.last_name,
                    "phone": user.phone_number,
                }
            }, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({
                "status": "2",
                "response": {
                    "error_code": "9999",
                    "error_message_us": "System error",
                    "error_message_vn": f"Lỗi hệ thống: {str(e)}"
                }
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class QuickSearch(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            query = request.query_params.get('q', '').strip()

            if not query or len(query) < 2:
                return Response({
                    "status": "1",
                    "response": {
                        "products": [],
                        "orders": [],
                        "customers": [],
                    }
                }, status=status.HTTP_200_OK)

            products = Product.objects.filter(
                Q(is_active=True),
                Q(name__icontains=query) | Q(sku__icontains=query)
            ).values('id', 'name', 'sku', 'bar_code', 'price')[:5]

            payments = Payment.objects.select_related('order').filter(
                Q(is_active=True),
                Q(order_code__icontains=query) | Q(order__buyer_name__icontains=query)
            )[:5]

            # Transform to dict with buyer_name from order
            payments_data = [
                {
                    'id': p.id,
                    'order_code': p.order_code,
                    'amount': float(p.amount),
                    'buyer_name': p.order.buyer_name if p.order and p.order.buyer_name else 'Khách lẻ',
                    'created_at': p.created_at.isoformat()
                }
                for p in payments
            ]

            customers = Customer.objects.filter(
                Q(is_active=True),
                Q(name__icontains=query) | Q(phone__icontains=query) | Q(
                    customer_code__icontains=query)
            ).values('id', 'customer_code', 'name', 'phone')[:5]

            return Response({
                "status": "1",
                "response": {
                    "products": list(products),
                    "orders": payments_data,
                    "customers": list(customers),
                }
            }, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({
                "status": "2",
                "response": {
                    "error_code": "9999",
                    "error_message_us": "System error",
                    "error_message_vn": f"Lỗi hệ thống: {str(e)}"
                }
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
