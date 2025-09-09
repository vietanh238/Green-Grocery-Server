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
        serializer = LoginSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.validated_data['user']
            if not user.is_active:
                return Response({
                    'status': '2',
                    'message': 'Account is not active'
                })

            refresh = RefreshToken.for_user(user)

            return Response({
                'status': '1',
                'data': {
                    'access': str(refresh.access_token),
                    'refresh': str(refresh),
                    'user': {
                        'id': user.id,
                        'phone_number': user.phone_number
                    }
                }
            })

        return Response({
            'status': '2',
            'message': 'Incorrect account'
        })