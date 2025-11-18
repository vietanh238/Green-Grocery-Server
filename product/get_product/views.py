from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from django.db.models import Q, F, Sum, Count
from core.models import Product
from .serializers import ProductListSerializer


class GetProductView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            search_query = request.GET.get('search', '').strip()
            category_id = request.GET.get('category_id', '').strip()
            stock_status = request.GET.get('stock_status', '').strip()
            sort_by = request.GET.get('sort_by', '-created_at')

            products = Product.objects.select_related(
                'category', 'supplier'
            ).filter(is_active=True)

            if search_query:
                products = products.filter(
                    Q(name__icontains=search_query) |
                    Q(sku__icontains=search_query) |
                    Q(bar_code__icontains=search_query)
                )

            if category_id:
                products = products.filter(category_id=category_id)

            if stock_status:
                if stock_status == 'out_of_stock':
                    products = products.filter(stock_quantity=0)
                elif stock_status == 'low_stock':
                    products = products.filter(
                        stock_quantity__gt=0,
                        stock_quantity__lte=F('reorder_point')
                    )
                elif stock_status == 'in_stock':
                    products = products.filter(
                        stock_quantity__gt=F('reorder_point'),
                        stock_quantity__lte=F('max_stock_level')
                    )
                elif stock_status == 'overstock':
                    products = products.filter(
                        stock_quantity__gt=F('max_stock_level')
                    )

            products = products.order_by(sort_by)

            serializer = ProductListSerializer(products, many=True)

            stats = {
                'total_products': products.count(),
                'low_stock_count': products.filter(
                    stock_quantity__gt=0,
                    stock_quantity__lte=F('reorder_point')
                ).count(),
                'out_of_stock_count': products.filter(stock_quantity=0).count(),
                'total_stock_value': products.aggregate(
                    total=Sum(F('stock_quantity') * F('cost_price'))
                )['total'] or 0
            }

            return Response({
                'status': '1',
                'response': serializer.data,
                'stats': stats
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
