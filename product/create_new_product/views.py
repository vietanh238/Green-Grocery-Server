from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from .serializer import ProductSerializer
from django.db import transaction
from ..models import Category


class CreateProduct(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        try:
            category_id = request.data.get('category')
            item_category = Category.objects.filter(name=category_id)
            if item_category.exists():
                category_id = item_category.first().id
            else:
                Category.objects.create(
                    name=request.data.get('category')
                )
                category_id = Category.objects.filter(
                    name=request.data.get('category')
                ).first().id
            data = request.data
            data['category_id'] = category_id
            serializer = ProductSerializer(data=data)
            if not serializer.is_valid():
                return Response({
                    'status': '2',
                    'response': serializer.errors
                }, status=status.HTTP_400_BAD_REQUEST)


            with transaction.atomic():
                product = serializer.save()

            return Response({
                'status': '1',
                'response': {
                    'message': 'Product created successfully.',
                    'product': serializer.data
                }
            }, status=status.HTTP_201_CREATED)

        except Exception as ex:
            return Response({
                'status': '2',
                'response': {
                    "error_code": "9999",
                    "error_message_us": "An internal server error occurred.",
                    "error_message_vn": "Lỗi hệ thống"
                }
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)