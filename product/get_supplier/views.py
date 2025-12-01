# product/supplier/views.py
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from core.models import Supplier
from .serializers import SupplierSerializer, SupplierCreateSerializer, SupplierUpdateSerializer


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


class UpdateSupplierView(APIView):
    """
    Cập nhật thông tin nhà cung cấp dựa theo supplier_code.
    Không cho phép thay đổi mã nhà cung cấp.
    """
    permission_classes = [IsAuthenticated]

    def put(self, request):
        try:
            supplier_code = request.data.get('supplier_code', '').strip()
            if not supplier_code:
                return Response({
                    'status': '2',
                    'response': {
                        'error_code': '003',
                        'error_message_us': 'Supplier code is required',
                        'error_message_vn': 'Thiếu mã nhà cung cấp'
                    }
                }, status=status.HTTP_400_BAD_REQUEST)

            try:
                supplier = Supplier.objects.get(
                    supplier_code=supplier_code, is_active=True
                )
            except Supplier.DoesNotExist:
                return Response({
                    'status': '2',
                    'response': {
                        'error_code': '004',
                        'error_message_us': 'Supplier not found',
                        'error_message_vn': 'Không tìm thấy nhà cung cấp'
                    }
                }, status=status.HTTP_404_NOT_FOUND)

            serializer = SupplierUpdateSerializer(
                supplier, data=request.data, partial=True
            )

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

            supplier = serializer.save(updated_by=request.user)

            return Response({
                'status': '1',
                'response': {
                    'message': 'Cập nhật nhà cung cấp thành công',
                    'supplier': SupplierSerializer(supplier).data
                }
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


class DeleteSupplierView(APIView):
    """
    Xóa (mềm) nhà cung cấp theo supplier_code.
    """
    permission_classes = [IsAuthenticated]

    def delete(self, request, supplier_code: str):
        try:
            supplier_code = (supplier_code or '').strip()
            try:
                supplier = Supplier.objects.get(
                    supplier_code=supplier_code, is_active=True
                )
            except Supplier.DoesNotExist:
                return Response({
                    'status': '2',
                    'response': {
                        'error_code': '004',
                        'error_message_us': 'Supplier not found',
                        'error_message_vn': 'Không tìm thấy nhà cung cấp'
                    }
                }, status=status.HTTP_404_NOT_FOUND)

            supplier.is_active = False
            supplier.updated_by = request.user
            supplier.save(update_fields=['is_active', 'updated_by', 'updated_at'])

            return Response({
                'status': '1',
                'response': {
                    'message': 'Xóa nhà cung cấp thành công'
                }
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
