from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from core.models import Category


class GetCategoryView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            categories = Category.objects.filter(is_active=True).order_by('sort_order', 'name')

            data = [
                {
                    'id': cat.id,
                    'name': cat.name,
                    'description': cat.description,
                    'parent_id': cat.parent_id,
                    'sort_order': cat.sort_order
                }
                for cat in categories
            ]

            return Response({
                'status': '1',
                'response': {
                    'data': data,
                    'total': len(data)
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