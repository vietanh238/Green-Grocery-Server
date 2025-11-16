from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from core.models import Product
from django.db.models import Case, When, Value, BooleanField
from django.db.models import F
from django.db.models.functions import TruncDate

class GetProduct(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            list_product = Product.objects.filter(is_active=True).annotate(
                is_reorder = Case(
                    When(stock_quantity__lte=F("reorder_point"),then=Value(True)),
                    default=Value(False),
                    output_field=BooleanField()
                ),
                name_category=F("category__name"),
                created_by_name= F("created_by__last_name"),
                updated_by_name= F("updated_by__last_name"),
                created_at_date=TruncDate('created_at')
            ).values(
                "name", "sku", "bar_code", "name_category", "unit",
                "price", "is_reorder", "stock_quantity", "cost_price",
                "created_by_name", "updated_by_name", "created_at_date"
            )
            list_product = list_product.order_by('stock_quantity')[:100]

            return Response({
                "status": "1",
                "response":list_product
            })

        except Exception as ex:
            return Response({
                "error_code": "9999",
                "error_message": "System error",
            })