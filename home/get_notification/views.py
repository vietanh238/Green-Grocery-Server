from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from django.utils import timezone

class GetNotificationsView(APIView):
    permission_classes =[IsAuthenticated]
    def get(self, request):
        try:
            message = []
            user = request.user
            if not user.is_change_pass:
                message.append({
                    'priority': '1',
                    'title': 'Thay đổi mật khẩu',
                    'message': 'Vui lòng đổi mật khẩu của bạn',
                    'time': timezone.now(),
                    'time_now': timezone.now(),
                })

            return Response({
                'status': '1',
                'response': {
                    'message': message
                }
            })
        except Exception as ex:
            return Response({
                'status': '2',
                'response': {
                    "error_code": "9999",
                    "error_message_us": "System error",
                    "error_message_vn": "Lỗi hệ thống"
                }
            })