from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from ..models import Category
from rest_framework.response import Response

class GetCategory(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            list_category = Category.objects.values('name', 'id')
            return Response({
                'status': '1',
                'response': {
                    'data': list_category
                }})
        except Exception as ex:
            return Response({
                'status': '2',
                'response': {
                    "error_code": "9999",
                    "error_message": "System error"
                }
            })