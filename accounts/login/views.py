from rest_framework.views import APIView
from .serializer import LoginSerializer, RegisterSerializer
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.permissions import IsAuthenticated

class LoginView(APIView):
    def post(self, request):
        try:
            serializer = LoginSerializer(data=request.data)
            if serializer.is_valid():
                user = serializer.validated_data['user']
                if not user.is_active:
                    return Response({
                        'status': '2',
                        'response': {
                            "error_code": "1",
                            "error_message_us": "User is not active",
                            "error_message_vn": "Tài khoản không còn hoạt động"
                        }
                    })

                refresh = RefreshToken.for_user(user)

                response = Response({
                    'status': '1',
                    'response': {
                        'access': str(refresh.access_token),
                        'user': {
                            'id': user.id,
                            'phone_number': user.phone_number
                        }
                    }
                })

                response.set_cookie(
                    key='refresh_token',
                    value=str(refresh),
                    httponly=True,
                    secure=True,
                    samesite='None',
                    max_age=7*24*60*60,
                    path='/api/account/refresh/'
                )

                return response

            else:
                return Response({
                    'status': '2',
                    'response': {
                        "error_code": "1",
                        "error_message_us": "Account incorrect",
                        "error_message_vn": "Tài khoản không chính xác"
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


class RegisterView(APIView):
    """API endpoint for user registration"""

    def post(self, request):
        try:
            serializer = RegisterSerializer(data=request.data)

            if serializer.is_valid():
                user = serializer.save()

                return Response({
                    'status': '1',
                    'response': {
                        'message': 'Đăng ký thành công',
                        'user': {
                            'id': user.id,
                            'phone_number': user.phone_number,
                            'first_name': user.first_name,
                            'last_name': user.last_name
                        }
                    }
                })

            else:
                # Get first error message
                errors = serializer.errors
                first_field = list(errors.keys())[0]
                first_error = errors[first_field][0]

                return Response({
                    'status': '2',
                    'response': {
                        "error_code": "1",
                        "error_message_us": str(first_error),
                        "error_message_vn": str(first_error)
                    }
                })

        except Exception as ex:
            print(f"Register error: {str(ex)}")  # For debugging
            return Response({
                'status': '2',
                'response': {
                    "error_code": "9999",
                    "error_message_us": "System error",
                    "error_message_vn": "Lỗi hệ thống"
                }
            })