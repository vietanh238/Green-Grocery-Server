from rest_framework.views import APIView
from .serializer import LoginSerializer
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.permissions import IsAuthenticated

class LoginView(APIView):
    # permission_classes = [IsAuthenticated]

    # def get(self, request):
    #     user = request.

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
                            "error_message": "User is not active"
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
                        "error_message": "Account incorrect"
                    }
                })

        except Exception as ex:
            return Response({
                'status': '2',
                'response': {
                    "error_code": "9999",
                    "error_message": "System error"
                }
            })
