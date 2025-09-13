from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.contrib.auth.hashers import check_password

class ChangePasswordView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        user = request.user
        old_password = request.data.get('old_password')
        new_password = request.data.get('new_password')

        if not old_password or not new_password:
            return Response({
                'status': '2',
                'response': {
                    'error_message_us': 'Missing password fields',
                    'error_message_vn': 'Thiếu thông tin mật khẩu'
                }
            })
        if not check_password(old_password, user.password):
            return Response({
                'status': '2',
                'response': {
                    'error_message_us': 'Old password incorrect',
                    'error_message_vn': 'Mật khẩu cũ không đúng'
                }
            })

        user.set_password(new_password)
        user.is_change_pass = True
        user.save()

        return Response({
            'status': '1',
            'response': {
                'user': user.id
            }
        })
