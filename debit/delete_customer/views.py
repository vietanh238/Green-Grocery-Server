from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from core.models import Customer, Debt
from django.db.models import Sum, F, ExpressionWrapper, DecimalField
from .serializer import DeleteCustomerSerializer


class DeleteCustomer(APIView):
    permission_classes = [IsAuthenticated]

    def delete(self, request):
        try:
            serializer = DeleteCustomerSerializer(data=request.data)

            if serializer.is_valid():
                customer_code = serializer.validated_data['customer_code']

                try:
                    customer = Customer.objects.get(
                        customer_code=customer_code,
                        is_active=True
                    )
                except Customer.DoesNotExist:
                    return Response({
                        "status": "2",
                        "response": {
                            "error_code": "002",
                            "error_message_us": "Customer not found",
                            "error_message_vn": "Khách hàng không tồn tại"
                        }
                    }, status=status.HTTP_404_NOT_FOUND)

                if customer.total_debt > 0:
                    return Response({
                        'status': '2',
                        'response': {
                            'error_code': '001',
                            'error_message_us': 'Cannot delete customer with outstanding debt',
                            'error_message_vn': f'Không thể xóa khách hàng vẫn còn nợ. Số nợ hiện tại: {float(customer.total_debt):,.0f} VND'
                        }
                    }, status=status.HTTP_400_BAD_REQUEST)

                customer.is_active = False
                customer.save()

                return Response({
                    "status": "1",
                    "response": {
                        "customer_code": customer.customer_code,
                        "customer_name": customer.name,
                        "message": "Xóa khách hàng thành công"
                    }
                }, status=status.HTTP_200_OK)
            else:
                return Response({
                    "status": "2",
                    "response": {
                        "error_code": "001",
                        "error_message_us": "Validation error",
                        "error_message_vn": "Dữ liệu không hợp lệ",
                        "errors": serializer.errors
                    }
                }, status=status.HTTP_400_BAD_REQUEST)

        except Exception as e:
            import traceback
            traceback.print_exc()
            return Response({
                "status": "2",
                "response": {
                    "error_code": "9999",
                    "error_message_us": "System error",
                    "error_message_vn": f"Lỗi hệ thống: {str(e)}"
                }
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
