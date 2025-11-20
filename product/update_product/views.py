from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from django.db import transaction
from django.utils import timezone
from core.models import Product, Category, Supplier
from core.services.inventory_service import InventoryService
from .serializer import ProductUpdateSerializer
from product.get_product.serializers import ProductListSerializer


class UpdateProductView(APIView):
    permission_classes = [IsAuthenticated]

    def put(self, request):
        try:
            user = request.user
            serializer = ProductUpdateSerializer(data=request.data)

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

            data = serializer.validated_data

            try:
                product = Product.objects.get(id=data['id'], is_active=True)
            except Product.DoesNotExist:
                return Response({
                    'status': '2',
                    'response': {
                        'error_code': '005',
                        'error_message_us': 'Product not found',
                        'error_message_vn': 'Không tìm thấy sản phẩm'
                    }
                }, status=status.HTTP_404_NOT_FOUND)

            if Product.objects.filter(sku=data['sku'], is_active=True).exclude(id=product.id).exists():
                return Response({
                    'status': '2',
                    'response': {
                        'error_code': '002',
                        'error_message_us': 'SKU already exists',
                        'error_message_vn': f"SKU '{data['sku']}' đã tồn tại trong hệ thống"
                    }
                }, status=status.HTTP_400_BAD_REQUEST)

            if Product.objects.filter(bar_code=data['barCode'], is_active=True).exclude(id=product.id).exists():
                return Response({
                    'status': '2',
                    'response': {
                        'error_code': '003',
                        'error_message_us': 'Barcode already exists',
                        'error_message_vn': f"Barcode '{data['barCode']}' đã tồn tại trong hệ thống"
                    }
                }, status=status.HTTP_400_BAD_REQUEST)

            with transaction.atomic():
                old_quantity = product.stock_quantity

                category_name = data['category']
                category, created = Category.objects.get_or_create(
                    name=category_name,
                    defaults={
                        'created_by': user,
                        'updated_by': user
                    }
                )

                supplier = None
                if data.get('supplierId'):
                    try:
                        supplier = Supplier.objects.get(
                            id=data['supplierId'],
                            is_active=True
                        )
                    except Supplier.DoesNotExist:
                        pass

                product.name = data['productName']
                product.sku = data['sku']
                product.bar_code = data['barCode']
                product.category = category
                product.supplier = supplier
                product.unit = data['unit']
                product.cost_price = data['costPrice']
                product.price = data['price']
                product.reorder_point = data['reorderPoint']
                product.max_stock_level = data['maxStockLevel']
                product.image = data.get('image', '')
                product.description = data.get('description', '')
                product.has_expiry = data.get('hasExpiry', False)
                product.shelf_life_days = data.get('shelfLifeDays')
                product.updated_by = user
                product.save()

                # Handle stock quantity change via inventory adjustment
                new_quantity = data['quantity']
                if new_quantity != old_quantity:
                    quantity_diff = new_quantity - old_quantity
                    InventoryService.create_transaction(
                        product=product,
                        transaction_type='adjustment',
                        quantity=quantity_diff,
                        unit_price=product.cost_price,
                        reference_type='manual_adjustment',
                        reference_id=product.id,
                        note=f'Điều chỉnh tồn kho từ {old_quantity} thành {new_quantity}',
                        user=user
                    )
                    if new_quantity > old_quantity:
                        product.last_restock_date = timezone.now()
                        product.save()

            product_data = ProductListSerializer(product).data

            return Response({
                'status': '1',
                'response': {
                    'message': 'Cập nhật sản phẩm thành công',
                    'product': product_data
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
