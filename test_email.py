"""
Script để test gửi email
Chạy: python test_email.py
"""
import os
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Server.settings')
django.setup()

from django.core.mail import send_mail
from django.conf import settings

def test_email():
    print("=" * 60)
    print("🔍 TESTING EMAIL CONFIGURATION")
    print("=" * 60)

    # Check settings
    print("\n📋 Email Settings:")
    print(f"   EMAIL_BACKEND: {settings.EMAIL_BACKEND}")
    print(f"   EMAIL_HOST: {settings.EMAIL_HOST}")
    print(f"   EMAIL_PORT: {settings.EMAIL_PORT}")
    print(f"   EMAIL_USE_TLS: {settings.EMAIL_USE_TLS}")
    print(f"   EMAIL_HOST_USER: {settings.EMAIL_HOST_USER}")
    print(f"   EMAIL_HOST_PASSWORD: {'*' * len(settings.EMAIL_HOST_PASSWORD) if settings.EMAIL_HOST_PASSWORD else 'NOT SET'}")
    print(f"   DEFAULT_FROM_EMAIL: {settings.DEFAULT_FROM_EMAIL}")

    # Check if configured
    if settings.EMAIL_HOST_USER == 'your-email@gmail.com':
        print("\n❌ LỖI: Email chưa được cấu hình!")
        print("   Vui lòng mở Server/Server/settings.py")
        print("   Và thay đổi:")
        print("   - EMAIL_HOST_USER = 'email-cua-ban@gmail.com'")
        print("   - EMAIL_HOST_PASSWORD = 'app-password-cua-ban'")
        print("\n📖 Xem hướng dẫn tại: Server/EMAIL_SETUP.md")
        return

    # Ask for test email
    print("\n" + "=" * 60)
    test_to_email = input("📧 Nhập email nhận test (để trống = gửi cho chính mình): ").strip()

    if not test_to_email:
        test_to_email = settings.EMAIL_HOST_USER

    print(f"\n📤 Đang gửi email test đến: {test_to_email}")
    print("   Vui lòng đợi...")

    try:
        # Send test email
        send_mail(
            subject='✅ Test Email - Green Grocery',
            message='Đây là email test từ hệ thống Green Grocery. Nếu bạn nhận được email này, cấu hình email đã thành công!',
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[test_to_email],
            fail_silently=False,
        )

        print("\n" + "=" * 60)
        print("✅ GỬI EMAIL THÀNH CÔNG!")
        print("=" * 60)
        print(f"📬 Kiểm tra hộp thư: {test_to_email}")
        print("   (Có thể trong Inbox hoặc Spam)")
        print("\n💡 Nếu không thấy email:")
        print("   1. Kiểm tra thư mục Spam")
        print("   2. Đợi vài phút (đôi khi chậm)")
        print("   3. Kiểm tra lại email nhận")

    except Exception as e:
        print("\n" + "=" * 60)
        print("❌ GỬI EMAIL THẤT BẠI!")
        print("=" * 60)
        print(f"Lỗi: {str(e)}\n")

        # Common errors
        if "Authentication" in str(e) or "Username and Password not accepted" in str(e):
            print("🔐 Lỗi xác thực:")
            print("   - Kiểm tra EMAIL_HOST_USER đúng chưa")
            print("   - Kiểm tra EMAIL_HOST_PASSWORD (phải là App Password, không phải mật khẩu Gmail)")
            print("   - Đảm bảo 2-Step Verification đã bật")
            print("\n📖 Xem hướng dẫn tạo App Password: Server/EMAIL_SETUP.md")

        elif "Connection" in str(e) or "timed out" in str(e):
            print("🌐 Lỗi kết nối:")
            print("   - Kiểm tra internet")
            print("   - Kiểm tra firewall có chặn port 587 không")
            print("   - Thử đổi EMAIL_PORT = 465 và EMAIL_USE_SSL = True")

        else:
            print("💡 Các bước kiểm tra:")
            print("   1. Mở Server/Server/settings.py")
            print("   2. Kiểm tra EMAIL_HOST_USER và EMAIL_HOST_PASSWORD")
            print("   3. Đảm bảo dùng App Password (16 ký tự)")
            print("   4. Xem hướng dẫn chi tiết: Server/EMAIL_SETUP.md")

if __name__ == '__main__':
    test_email()

