from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from django.db import transaction
from django.db.models import F
from django.utils import timezone
from core.models import Product, Category, Supplier
from .serializer import BulkCreateProductsSerializer


class BulkCreateProductsView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        try:
            user = request.user
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
            update_count = 0
            errors = []

            barcodes = [p['barCode'] for p in products_data]
            skus = [p['sku'] for p in products_data]

            existing_products_by_barcode = {
                p.bar_code: p for p in Product.objects.filter(
                    bar_code__in=barcodes,
                    is_active=True
                )
            }
            existing_products_by_sku = {
                p.sku: p for p in Product.objects.filter(
                    sku__in=skus,
                    is_active=True
                )
            }

            category_cache = {}
            supplier_cache = {}
            products_to_create = []
            products_to_update = []

            for index, product_data in enumerate(products_data):
                try:
                    barcode = product_data['barCode']
                    sku = product_data['sku']
                    category_name = product_data['category']

                    existing_product = None
                    if barcode in existing_products_by_barcode:
                        existing_product = existing_products_by_barcode[barcode]
                    elif sku in existing_products_by_sku:
                        existing_product = existing_products_by_sku[sku]

                    if existing_product:
                        existing_product.stock_quantity = F(
                            'stock_quantity') + product_data['quantity']
                        existing_product.price = product_data['price']
                        existing_product.cost_price = product_data['costPrice']
                        existing_product.updated_by = user
                        existing_product.last_restock_date = timezone.now()

                        products_to_update.append(existing_product)
                        update_count += 1

                    else:
                        if category_name not in category_cache:
                            category, created = Category.objects.get_or_create(
                                name=category_name,
                                defaults={
                                    'created_by': user,
                                    'updated_by': user
                                }
                            )
                            category_cache[category_name] = category

                        supplier = None
                        supplier_name = product_data.get(
                            'supplierName', '').strip()
                        if supplier_name:
                            if supplier_name not in supplier_cache:
                                try:
                                    supplier = Supplier.objects.get(
                                        name=supplier_name,
                                        is_active=True
                                    )
                                    supplier_cache[supplier_name] = supplier
                                except Supplier.DoesNotExist:
                                    pass
                            else:
                                supplier = supplier_cache[supplier_name]

                        products_to_create.append(Product(
                            name=product_data['name'],
                            sku=sku,
                            bar_code=barcode,
                            category=category_cache[category_name],
                            supplier=supplier,
                            unit=product_data['unit'],
                            cost_price=product_data['costPrice'],
                            price=product_data['price'],
                            stock_quantity=product_data['quantity'],
                            reorder_point=product_data.get('reorderPoint', 10),
                            max_stock_level=product_data.get(
                                'maxStockLevel', 1000),
                            has_expiry=product_data.get('hasExpiry', False),
                            shelf_life_days=product_data.get('shelfLifeDays'),
                            last_restock_date=timezone.now(
                            ) if product_data['quantity'] > 0 else None,
                            created_by=user,
                            updated_by=user
                        ))

                except Exception as e:
                    failed_count += 1
                    errors.append({
                        'row': index + 1,
                        'product': product_data.get('name', 'Unknown'),
                        'sku': product_data.get('sku', 'Unknown'),
                        'message': str(e)
                    })

            with transaction.atomic():
                if products_to_create:
                    Product.objects.bulk_create(
                        products_to_create, batch_size=500)
                    success_count = len(products_to_create)

                if products_to_update:
                    for product in products_to_update:
                        product.save()

            return Response({
                'status': '1',
                'response': {
                    'success': success_count,
                    'updated': update_count,
                    'failed': failed_count,
                    'total': len(products_data),
                    'errors': errors,
                    'message': f'Thêm mới {success_count} sản phẩm, cập nhật {update_count} sản phẩm'
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
