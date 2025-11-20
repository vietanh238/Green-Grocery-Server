"""
Test email nhanh với settings.py mới
"""
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# Copy từ settings.py mới
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 587
EMAIL_USER = 'gocdevnhalam@gmail.com'
EMAIL_PASSWORD = 'ztev gezq lcot axyt'

print("=" * 70)
print("🔍 TEST EMAIL VỚI APP PASSWORD MỚI")
print("=" * 70)
print(f"\n📧 Email: {EMAIL_USER}")
print(f"🔐 Password: {'*' * 16} ({len(EMAIL_PASSWORD.replace(' ', ''))} ký tự)")

# Check format
if len(EMAIL_PASSWORD.replace(' ', '')) == 16:
    print("✅ App Password đúng định dạng!")
else:
    print(f"⚠️  Password có {len(EMAIL_PASSWORD.replace(' ', ''))} ký tự")

# Test email (gửi cho chính mình)
test_to = EMAIL_USER

print(f"\n📤 Đang gửi email test đến: {test_to}")
print("⏳ Đang kết nối Gmail SMTP...\n")

try:
    # Tạo email
    msg = MIMEMultipart()
    msg['From'] = 'Green Grocery <noreply@green-grocery.io.vn>'
    msg['To'] = test_to
    msg['Subject'] = '✅ [TEST THÀNH CÔNG] - Green Grocery System'

    body = """
╔══════════════════════════════════════════════════════════╗
║            ✅ CẤU HÌNH EMAIL THÀNH CÔNG!                 ║
╚══════════════════════════════════════════════════════════╝

Xin chào!

Nếu bạn nhận được email này, có nghĩa là hệ thống Green Grocery
đã được cấu hình email THÀNH CÔNG! 🎉

Bây giờ bạn có thể:
✅ Tự động gửi email đơn đặt hàng cho nhà cung cấp
✅ Gửi thông báo cho khách hàng
✅ Nhận cảnh báo tồn kho qua email

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📧 Email được gửi từ: Green Grocery Management System
🕐 Thời gian: Vừa xong
🔐 Sử dụng: Gmail SMTP với App Password

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Chúc bạn kinh doanh thành công! 🚀

---
Green Grocery © 2024
Hệ thống Quản lý Tạp hóa Thông minh
    """

    msg.attach(MIMEText(body, 'plain', 'utf-8'))

    # Kết nối và gửi
    server = smtplib.SMTP(EMAIL_HOST, EMAIL_PORT, timeout=10)
    server.starttls()
    server.login(EMAIL_USER, EMAIL_PASSWORD)
    server.send_message(msg)
    server.quit()

    print("=" * 70)
    print("✅✅✅ GỬI EMAIL THÀNH CÔNG! ✅✅✅")
    print("=" * 70)
    print(f"\n📬 Email đã được gửi đến: {test_to}")
    print("\n💡 Kiểm tra hộp thư ngay:")
    print("   - Mở Gmail: https://mail.google.com")
    print("   - Tìm email với subject: '[TEST THÀNH CÔNG]'")
    print("   - Nếu không thấy trong Inbox → Check Spam")
    print("\n🎉 HỆ THỐNG ĐÃ SẴN SÀNG GỬI EMAIL TỰ ĐỘNG!")

except smtplib.SMTPAuthenticationError as e:
    print("=" * 70)
    print("❌ LỖI XÁC THỰC")
    print("=" * 70)
    print(f"Chi tiết: {str(e)}\n")
    print("🔴 App Password có thể:")
    print("   - Sai mã (copy sai)")
    print("   - Đã bị revoke")
    print("   - 2-Step chưa bật đủ lâu")
    print("\n✅ Thử:")
    print("   1. Tạo lại App Password mới: https://myaccount.google.com/apppasswords")
    print("   2. Copy cẩn thận (bỏ khoảng trắng)")
    print("   3. Update lại settings.py")

except Exception as e:
    print("=" * 70)
    print("❌ LỖI")
    print("=" * 70)
    print(f"Loại: {type(e).__name__}")
    print(f"Chi tiết: {str(e)}")

print("\n" + "=" * 70)

