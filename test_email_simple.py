"""
Test email đơn giản - Chạy ngay để xem lỗi
"""
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# Thông tin email (copy từ settings.py)
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 587
EMAIL_USER = 'gocdevnhalam@gmail.com'
EMAIL_PASSWORD = 'Test@2003'  # Đây có phải App Password không?

print("=" * 70)
print("🔍 ĐANG TEST GỬI EMAIL...")
print("=" * 70)
print(f"\n📧 Email gửi từ: {EMAIL_USER}")
print(f"🔐 Password: {'*' * len(EMAIL_PASSWORD)} ({len(EMAIL_PASSWORD)} ký tự)")

# Check password format
if len(EMAIL_PASSWORD) == 16 or (len(EMAIL_PASSWORD) == 19 and EMAIL_PASSWORD.count(' ') == 3):
    print("✅ Password có vẻ là App Password (16-19 ký tự)")
else:
    print(f"⚠️  Password chỉ có {len(EMAIL_PASSWORD)} ký tự - KHÔNG PHẢI App Password!")
    print("   → App Password phải có 16 ký tự (hoặc 19 ký tự nếu có khoảng trắng)")
    print("   → Ví dụ: 'abcd efgh ijkl mnop' hoặc 'abcdefghijklmnop'")

# Hỏi email nhận
print("\n" + "=" * 70)
test_to = input("📬 Nhập email nhận (Enter = gửi cho chính mình): ").strip()
if not test_to:
    test_to = EMAIL_USER

print(f"\n📤 Đang thử gửi email đến: {test_to}")
print("⏳ Vui lòng đợi...\n")

try:
    # Tạo email
    msg = MIMEMultipart()
    msg['From'] = EMAIL_USER
    msg['To'] = test_to
    msg['Subject'] = '✅ Test Email - Green Grocery'

    body = """
    Chào bạn!

    Đây là email test từ hệ thống Green Grocery.

    Nếu bạn nhận được email này, cấu hình email đã THÀNH CÔNG! ✅

    ---
    Green Grocery Management System
    """

    msg.attach(MIMEText(body, 'plain'))

    # Kết nối và gửi
    print("🔌 Đang kết nối đến Gmail SMTP...")
    server = smtplib.SMTP(EMAIL_HOST, EMAIL_PORT)
    server.set_debuglevel(0)  # Tắt debug để dễ đọc

    print("🔒 Đang bắt đầu TLS...")
    server.starttls()

    print("🔐 Đang đăng nhập...")
    server.login(EMAIL_USER, EMAIL_PASSWORD)

    print("📨 Đang gửi email...")
    server.send_message(msg)

    print("🔌 Đang đóng kết nối...")
    server.quit()

    print("\n" + "=" * 70)
    print("✅✅✅ GỬI EMAIL THÀNH CÔNG! ✅✅✅")
    print("=" * 70)
    print(f"\n📬 Kiểm tra hộp thư: {test_to}")
    print("\n💡 Lưu ý:")
    print("   - Email có thể trong Inbox hoặc Spam")
    print("   - Đợi vài giây để email đến")
    print("   - Subject: '✅ Test Email - Green Grocery'")

except smtplib.SMTPAuthenticationError as e:
    print("\n" + "=" * 70)
    print("❌ LỖI XÁC THỰC (Authentication Error)")
    print("=" * 70)
    print(f"Chi tiết: {str(e)}\n")
    print("🔴 NGUYÊN NHÂN:")
    print("   1. PASSWORD SAI - Bạn đang dùng mật khẩu Gmail thường!")
    print("   2. Chưa bật 2-Step Verification")
    print("   3. Chưa tạo App Password\n")
    print("✅ GIẢI PHÁP:")
    print("   Bước 1: Bật 2-Step Verification")
    print("           → https://myaccount.google.com/security")
    print("\n   Bước 2: Tạo App Password (16 ký tự)")
    print("           → https://myaccount.google.com/apppasswords")
    print("           → Chọn: Mail → Other (Custom) → 'Green Grocery'")
    print("           → Copy mã 16 ký tự (ví dụ: abcd efgh ijkl mnop)")
    print("\n   Bước 3: Cập nhật Server/Server/settings.py")
    print("           EMAIL_HOST_PASSWORD = 'abcd efgh ijkl mnop'")
    print("\n   Bước 4: Chạy lại script này để test")

except smtplib.SMTPException as e:
    print("\n" + "=" * 70)
    print("❌ LỖI SMTP")
    print("=" * 70)
    print(f"Chi tiết: {str(e)}\n")
    print("💡 Có thể do:")
    print("   - Kết nối internet không ổn định")
    print("   - Firewall chặn port 587")
    print("   - Gmail tạm thời block")

except Exception as e:
    print("\n" + "=" * 70)
    print("❌ LỖI KHÔNG XÁC ĐỊNH")
    print("=" * 70)
    print(f"Chi tiết: {str(e)}\n")
    print(f"Loại lỗi: {type(e).__name__}")

print("\n" + "=" * 70)

