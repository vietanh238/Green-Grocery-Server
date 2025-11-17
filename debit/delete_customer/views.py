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
                        "status": "9999",
                        "error_message": "Khách hàng không tồn tại"
                    }, status=status.HTTP_404_NOT_FOUND)
                if customer.total_debt != 0:
                    return Response({
                        'status': '2',
                        'error_code': 1
                    })
                customer.delete()
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
                    "status": "9999",
                    "error_message": "Dữ liệu không hợp lệ",
                    "errors": serializer.errors
                }, status=status.HTTP_400_BAD_REQUEST)

        except Exception as e:
            return Response({
                "status": "9999",
                "error_message": f"System error: {str(e)}"
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
