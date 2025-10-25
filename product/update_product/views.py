from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView
from rest_framework.response import Response
from ..models import Product, Category
from .serializer import UpdateProductSerializer
from django.db import transaction


class UpdateProductView(APIView):
    permission_classes = [IsAuthenticated]

    def put(self, request):
        bar_code = request.data.get('barCode')
        serializer = UpdateProductSerializer
        if not bar_code:
            return Response({
                'status': '2',
                'error_message': 'Bar code is not exist'
            })
        item_category = Category.objects.filter(name=request.data.get('category'))
        if item_category.exists():
            category = item_category.first()
        else:
            Category.objects.create(
                name=request.data.get('category')
            )
            category = Category.objects.filter(
                name=request.data.get('category')
            ).first()
        product = Product.objects.filter(bar_code=bar_code).first()
        if not product:
            return Response({
                'status': '2',
                'error_message': 'Product does not exist'
            })

        validate_require = serializer.validateData(request.data)
        if validate_require == 1:
            return Response({
                'status': '2',
                'error_message': 'Please fill in the required fields'
            })

        with transaction.atomic():
            try:
                product.name = request.data.get('productName')
                product.sku = request.data.get('sku')
                product.price = request.data.get('price')
                product.cost_price = request.data.get('costPrice')
                product.unit = request.data.get('unit')
                product.category_id = category
                product.stock_quantity = request.data.get('quantity')
                product.save()

                return Response({
                    'status': '1',
                    'response': {
                        'product': product.bar_code
                    }
                })
            except Exception as ex:
                return Response({
                    'status': '2',
                    'error_message': 'System error'
                })
