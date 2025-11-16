from rest_framework import serializers
from django.contrib.auth import authenticate
from ..models import User

class LoginSerializer(serializers.Serializer):
    phone_number = serializers.CharField()
    password = serializers.CharField(write_only=True)

    def validate(self, data):
        phone_number = data.get('phone_number')
        password = data.get('password')

        if phone_number and password:
            user = authenticate(request=self.context.get('request'), phone_number=phone_number, password=password)
            if not user:
                raise serializers.ValidationError('Invalid phone number or password.')
            data['user'] = user
        else:
            raise serializers.ValidationError('Must include both phone number and password.')
        return data


class RegisterSerializer(serializers.Serializer):
    phone_number = serializers.CharField(max_length=15)
    password = serializers.CharField(write_only=True, min_length=6)
    first_name = serializers.CharField(max_length=150, required=False, allow_blank=True)
    last_name = serializers.CharField(max_length=150, required=False, allow_blank=True)

    def validate_phone_number(self, value):
        """Validate phone number is unique"""
        value = str(value).strip()

        if len(value) < 10:
            raise serializers.ValidationError('Số điện thoại phải có ít nhất 10 số')

        if User.objects.filter(phone_number=value).exists():
            raise serializers.ValidationError('Số điện thoại đã được đăng ký')

        return value

    def validate_password(self, value):
        """Validate password strength"""
        if len(value) < 6:
            raise serializers.ValidationError('Mật khẩu phải có ít nhất 6 ký tự')
        return value

    def create(self, validated_data):
        """Create new user"""
        phone_number = validated_data['phone_number']
        password = validated_data['password']
        first_name = validated_data.get('first_name', '')
        last_name = validated_data.get('last_name', '')

        user = User.objects.create_user(
            phone_number=phone_number,
            password=password,
            first_name=first_name,
            last_name=last_name
        )

        return user