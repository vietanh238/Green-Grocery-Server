# product/supplier/views.py
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from core.models import Supplier
from .serializers import SupplierSerializer, SupplierCreateSerializer


class GetSuppliersView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            suppliers = Supplier.objects.filter(
                is_active=True).order_by('-created_at')
            serializer = SupplierSerializer(suppliers, many=True)

            return Response({
                'status': '1',
                'response': serializer.data
            }, status=status.HTTP_200_OK)

        except Exception as ex:
            return Response({
                'status': '2',
                'response': {
                    'error_code': '9999',
                    'error_message_us': 'An internal server error occurred.',
                    'error_message_vn': f'Lỗi hệ thống: {str(ex)}'
                }
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# product/supplier/views.py
class CreateSupplierView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        try:
            serializer = SupplierCreateSerializer(data=request.data)

            if not serializer.is_valid():
                return Response({
                    'status': '2',
                    'response': {
                        'error_code': '001',
                        'error_message_us': 'Validation error',
                        'error_message_vn': 'Dữ liệu không hợp lệ',
                        'errors': serializer.errors
                    }
                }, status=status.HTTP_400_BAD_REQUEST)

            if Supplier.objects.filter(supplier_code=serializer.validated_data['supplier_code']).exists():
                return Response({
                    'status': '2',
                    'response': {
                        'error_code': '002',
                        'error_message_us': 'Supplier code already exists',
                        'error_message_vn': 'Mã nhà cung cấp đã tồn tại'
                    }
                }, status=status.HTTP_400_BAD_REQUEST)

            # Sử dụng serializer.save() để tự động handle created_by, updated_by
            supplier = serializer.save(
                created_by=request.user,
                updated_by=request.user
            )

            return Response({
                'status': '1',
                'response': {
                    'message': 'Thêm nhà cung cấp thành công',
                    'supplier': SupplierSerializer(supplier).data
                }
            }, status=status.HTTP_201_CREATED)

        except Exception as ex:
            return Response({
                'status': '2',
                'response': {
                    'error_code': '9999',
                    'error_message_us': 'An internal server error occurred.',
                    'error_message_vn': f'Lỗi hệ thống: {str(ex)}'
                }
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
