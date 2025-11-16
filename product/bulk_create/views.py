from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from .serializer import BulkCreateProductsSerializer
from core.models import Product, Category
from django.db import transaction
from django.db.models import Q


class BulkCreateProducts(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        try:
            serializer = BulkCreateProductsSerializer(data=request.data)

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

            products_data = serializer.validated_data['products']

            success_count = 0
            failed_count = 0
            errors = []

            existing_barcodes = set(
                Product.objects.filter(
                    bar_code__in=[p['bar_code'] for p in products_data]
                ).values_list('bar_code', flat=True)
            )

            existing_skus = set(
                Product.objects.filter(
                    sku__in=[p['sku'] for p in products_data]
                ).values_list('sku', flat=True)
            )

            category_cache = {}
            products_to_create = []

            for product_data in products_data:
                try:
                    barcode = product_data['bar_code']
                    sku = product_data['sku']


                    if barcode in existing_barcodes:
                        failed_count += 1
                        errors.append({
                            'product': product_data['name'],
                            'message': f'Barcode {barcode} đã tồn tại trong hệ thống'
                        })
                        continue

                    if sku in existing_skus:
                        failed_count += 1
                        errors.append({
                            'product': product_data['name'],
                            'message': f'SKU {sku} đã tồn tại trong hệ thống'
                        })
                        continue

                    category_name = product_data.pop('category')

                    if category_name not in category_cache:
                        category, created = Category.objects.get_or_create(
                            name=category_name
                        )
                        category_cache[category_name] = category

                    product_data['category_id'] = category_cache[category_name]

                    products_to_create.append(Product(**product_data))

                    existing_barcodes.add(barcode)
                    existing_skus.add(sku)

                except Exception as e:
                    failed_count += 1
                    errors.append({
                        'product': product_data.get('name', 'Unknown'),
                        'message': str(e)
                    })

            if products_to_create:
                with transaction.atomic():
                    Product.objects.bulk_create(products_to_create)
                    success_count = len(products_to_create)

            return Response({
                'status': '1',
                'response': {
                    'success': success_count,
                    'failed': failed_count,
                    'total': len(products_data),
                    'errors': errors
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
