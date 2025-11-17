from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from core.models import Product


class DeleteProductView(APIView):
    permission_classes = [IsAuthenticated]

    def delete(self, request, bar_code):
        try:
            user = request.user

            try:
                product = Product.objects.get(
                    bar_code=bar_code, is_active=True)
            except Product.DoesNotExist:
                return Response({
                    'status': '2',
                    'response': {
                        'error_code': '005',
                        'error_message_us': 'Product not found',
                        'error_message_vn': 'Không tìm thấy sản phẩm'
                    }
                }, status=status.HTTP_404_NOT_FOUND)

            product.is_active = False
            product.updated_by = user
            product.save()

            return Response({
                'status': '1',
                'response': {
                    'message': 'Xóa sản phẩm thành công'
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
