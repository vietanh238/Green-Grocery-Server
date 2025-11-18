from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from django.db import transaction
from django.utils import timezone
from core.models import Product, Category, Supplier
from .serializer import ProductCreateSerializer
from product.get_product.serializers import ProductListSerializer


class CreateProductView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        try:
            user = request.user
            serializer = ProductCreateSerializer(data=request.data)

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

            if Product.objects.filter(sku=data['sku'], is_active=True).exists():
                return Response({
                    'status': '2',
                    'response': {
                        'error_code': '002',
                        'error_message_us': 'SKU already exists',
                        'error_message_vn': f"SKU '{data['sku']}' đã tồn tại trong hệ thống"
                    }
                }, status=status.HTTP_400_BAD_REQUEST)

            if Product.objects.filter(bar_code=data['barCode'], is_active=True).exists():
                return Response({
                    'status': '2',
                    'response': {
                        'error_code': '003',
                        'error_message_us': 'Barcode already exists',
                        'error_message_vn': f"Barcode '{data['barCode']}' đã tồn tại trong hệ thống"
                    }
                }, status=status.HTTP_400_BAD_REQUEST)

            with transaction.atomic():
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

                product = Product.objects.create(
                    name=data['productName'],
                    sku=data['sku'],
                    bar_code=data['barCode'],
                    category=category,
                    supplier=supplier,
                    unit=data['unit'],
                    cost_price=data['costPrice'],
                    price=data['price'],
                    stock_quantity=data['quantity'],
                    reorder_point=data['reorderPoint'],
                    max_stock_level=data['maxStockLevel'],
                    image=data.get('image', ''),
                    description=data.get('description', ''),
                    has_expiry=data.get('hasExpiry', False),
                    shelf_life_days=data.get('shelfLifeDays'),
                    last_restock_date=timezone.now(
                    ) if data['quantity'] > 0 else None,
                    created_by=user,
                    updated_by=user
                )

            product_data = ProductListSerializer(product).data

            return Response({
                'status': '1',
                'response': {
                    'message': 'Thêm sản phẩm thành công',
                    'product': product_data
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
