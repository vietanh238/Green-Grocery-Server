from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from core.models import Customer
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from django.db.models import Sum, Max, F, ExpressionWrapper, DecimalField, When, Case, Value, CharField, Q, BooleanField
from django.utils.timezone import now
import uuid
from .serializer import CustomerSerializer

class CreateCustomer(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        try:
            serializer = CustomerSerializer()
            error_code = serializer.validate(data=request.data)
            if error_code != 0:
                return Response({
                    'status': '2',
                    'response': {
                        'error_code': str(error_code),
                        'error_message_us': 'Validation error',
                        'error_message_vn': 'Dữ liệu không hợp lệ'
                    }
                })

            customer_code = str(uuid.uuid4())
            customer = Customer.objects.create(
                customer_code=customer_code,
                name=request.data.get('name'),
                phone=request.data.get('phone'),
                address=request.data.get('address', '')
            )

            return Response({
                "status": "1",
                "response": {
                    "id": customer.id,
                    "customer_code": customer.customer_code,
                    "name": customer.name,
                    "phone": customer.phone,
                    "address": customer.address,
                    "created_at": customer.created_at
                }
            }, status=status.HTTP_201_CREATED)

        except Exception as e:
            return Response({
                "status": "2",
                "response": {
                    "error_code": "9999",
                    "error_message_us": "System error",
                    "error_message_vn": f"Lỗi hệ thống: {str(e)}"
                }
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
