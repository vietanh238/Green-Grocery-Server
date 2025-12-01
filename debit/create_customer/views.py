from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from core.models import Customer
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
                error_messages = {
                    '1': 'Tên khách hàng không được để trống',
                    '2': 'Số điện thoại đã được đăng ký trong hệ thống',
                    '3': 'Số điện thoại không được để trống',
                }
                return Response({
                    'status': '2',
                    'response': {
                        'error_code': str(error_code),
                        'error_message_us': 'Validation error',
                        'error_message_vn': error_messages.get(str(error_code), 'Dữ liệu không hợp lệ')
                    }
                }, status=status.HTTP_400_BAD_REQUEST)

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
