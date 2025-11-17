# product/get_product/views.py
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from core.models import Product
from .serializers import ProductListSerializer


class GetProductView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            products = Product.objects.select_related(
                'category', 'supplier'
            ).filter(is_active=True)

            serializer = ProductListSerializer(products, many=True)

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
