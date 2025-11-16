from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from core.models import Product, Category
from django.db import transaction


class DeleteProductView(APIView):
    permission_classes = [IsAuthenticated]

    def delete(self, request, bar_code):
        if not bar_code:
            return Response({
                'status': '2',
                'error_code': '1',
                'error_message': 'Bar code is not exits'
            })
        try:
            product = Product.objects.filter(bar_code=bar_code).first()
            with transaction.atomic():
                if product:
                    product.is_active = False;
                    product.save()
                    return Response({
                        'status': '1',
                        'response': 'Delete successfully'
                    })
                else:
                    return Response({
                        'status': '2',
                        'error_code': '2',
                        'error_message': 'Product not found'
                    })

        except:
            return Response({
                'status': '2',
                'error_code': '9999',
                'error_message': 'System error'
            })
