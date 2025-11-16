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
            serializer = CustomerSerializer(data=request.data)

            if serializer.is_valid():
                customer_code = str(uuid.uuid4())

                customer = Customer.objects.create(
                    customer_code=customer_code,
                    name=serializer.validated_data['name'],
                    phone=serializer.validated_data['phone'],
                    address=serializer.validated_data.get('address', '')
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
            else:
                return Response({
                    "status": "9999",
                    "error_message": "Dữ liệu không hợp lệ",
                    "errors": serializer.errors
                }, status=status.HTTP_400_BAD_REQUEST)

        except Exception as e:
            return Response({
                "status": "9999",
                "error_message": f"System error: {str(e)}"
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
