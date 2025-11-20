"""
Test gửi email đến nhà cung cấp
"""
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders

# Copy từ settings.py
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 587
FROM_EMAIL = 'gocdevnhalam@gmail.com'
EMAIL_PASSWORD = 'ztev gezq lcot axyt'

# Email nhà cung cấp
SUPPLIER_EMAIL = 'vietanh.duong.238@gmail.com'

print("=" * 70)
print("📧 TEST GỬI EMAIL ĐẾN NHÀ CUNG CẤP")
print("=" * 70)
print(f"\n✉️  Từ (FROM): {FROM_EMAIL}")
print(f"📬 Đến (TO): {SUPPLIER_EMAIL}")
print(f"\n⏳ Đang gửi...\n")

try:
    # Tạo email HTML đẹp
    msg = MIMEMultipart('alternative')
    msg['From'] = f'Green Grocery <{FROM_EMAIL}>'
    msg['To'] = SUPPLIER_EMAIL
    msg['Subject'] = '🛒 Đơn đặt hàng #PO20241120TEST - Green Grocery'
    
    # HTML content
    html_content = """
<!DOCTYPE html>
<html lang="vi">
<head>
    <meta charset="UTF-8">
    <style>
        body {
            font-family: 'Segoe UI', Arial, sans-serif;
            line-height: 1.6;
            color: #333;
            background-color: #f4f4f4;
            margin: 0;
            padding: 0;
        }
        .email-container {
            max-width: 650px;
            margin: 20px auto;
            background: white;
            border-radius: 12px;
            overflow: hidden;
            box-shadow: 0 4px 12px rgba(0,0,0,0.1);
        }
        .header {
            background: linear-gradient(135deg, #22c55e, #16a34a);
            color: white;
            padding: 30px;
            text-align: center;
        }
        .header h1 {
            margin: 0;
            font-size: 28px;
        }
        .content {
            padding: 30px;
        }
        .info-grid {
            background: #f9fafb;
            padding: 20px;
            border-radius: 8px;
            margin: 20px 0;
        }
        .info-row {
            display: flex;
            padding: 8px 0;
        }
        .info-label {
            font-weight: 600;
            color: #6b7280;
            width: 140px;
        }
        .info-value {
            color: #1a1a1a;
        }
        table {
            width: 100%;
            border-collapse: collapse;
            margin: 20px 0;
        }
        th {
            background: #f9fafb;
            padding: 12px;
            text-align: left;
            font-weight: 600;
            border-bottom: 2px solid #e5e7eb;
        }
        td {
            padding: 12px;
            border-bottom: 1px solid #f3f4f6;
        }
        .summary {
            background: linear-gradient(135deg, #f0fdf4, #dcfce7);
            padding: 20px;
            border-radius: 8px;
            margin-top: 20px;
            border: 2px solid #22c55e;
        }
        .total {
            font-size: 20px;
            font-weight: 700;
            color: #22c55e;
            text-align: right;
            margin-top: 10px;
            padding-top: 10px;
            border-top: 2px solid #22c55e;
        }
        .footer {
            background: #f9fafb;
            padding: 25px;
            text-align: center;
            color: #6b7280;
            border-top: 1px solid #e5e7eb;
        }
        .badge {
            display: inline-block;
            padding: 4px 10px;
            background: #dcfce7;
            color: #16a34a;
            border-radius: 6px;
            font-size: 12px;
            font-weight: 600;
        }
    </style>
</head>
<body>
    <div class="email-container">
        <div class="header">
            <h1>🛒 Đơn Đặt Hàng Mới</h1>
            <div style="font-size: 18px; margin-top: 10px;">
                Mã đơn: <strong>PO20241120TEST</strong>
            </div>
        </div>

        <div class="content">
            <h2 style="color: #22c55e; margin-bottom: 15px;">📋 Thông tin đơn hàng</h2>
            
            <div class="info-grid">
                <div class="info-row">
                    <div class="info-label">Nhà cung cấp:</div>
                    <div class="info-value"><strong>Công ty bạn</strong></div>
                </div>
                <div class="info-row">
                    <div class="info-label">Ngày tạo đơn:</div>
                    <div class="info-value">20/11/2024 14:30</div>
                </div>
                <div class="info-row">
                    <div class="info-label">Người tạo:</div>
                    <div class="info-value">Green Grocery Store</div>
                </div>
                <div class="info-row">
                    <div class="info-label">Ngày dự kiến:</div>
                    <div class="info-value">
                        <strong>25/11/2024</strong>
                        <span class="badge">Cần giao trước ngày này</span>
                    </div>
                </div>
            </div>

            <h2 style="color: #22c55e; margin: 30px 0 15px 0;">📦 Danh sách sản phẩm (3 sản phẩm)</h2>
            
            <table>
                <thead>
                    <tr>
                        <th style="width: 50px; text-align: center;">#</th>
                        <th>Sản phẩm</th>
                        <th style="text-align: center;">Số lượng</th>
                        <th style="text-align: right;">Đơn giá</th>
                        <th style="text-align: right;">Thành tiền</th>
                    </tr>
                </thead>
                <tbody>
                    <tr>
                        <td style="text-align: center;">1</td>
                        <td><strong>Coca Cola 330ml</strong></td>
                        <td style="text-align: center;"><strong>50</strong> thùng</td>
                        <td style="text-align: right;">10,000đ</td>
                        <td style="text-align: right;"><strong>500,000đ</strong></td>
                    </tr>
                    <tr>
                        <td style="text-align: center;">2</td>
                        <td><strong>Pepsi 330ml</strong></td>
                        <td style="text-align: center;"><strong>30</strong> thùng</td>
                        <td style="text-align: right;">10,000đ</td>
                        <td style="text-align: right;"><strong>300,000đ</strong></td>
                    </tr>
                    <tr>
                        <td style="text-align: center;">3</td>
                        <td><strong>Snack Oishi</strong></td>
                        <td style="text-align: center;"><strong>100</strong> gói</td>
                        <td style="text-align: right;">5,000đ</td>
                        <td style="text-align: right;"><strong>500,000đ</strong></td>
                    </tr>
                </tbody>
            </table>

            <div class="summary">
                <div style="display: flex; justify-content: space-between; padding: 8px 0;">
                    <span>Tổng số lượng:</span>
                    <strong>180 đơn vị</strong>
                </div>
                <div class="total">
                    TỔNG GIÁ TRỊ ĐƠN HÀNG: 1,300,000đ
                </div>
            </div>

            <div style="background: #fffbeb; border-left: 4px solid #f59e0b; padding: 15px; margin-top: 20px; border-radius: 4px;">
                <h3 style="margin: 0 0 8px 0; color: #f59e0b; font-size: 14px;">📝 Ghi chú:</h3>
                <p style="margin: 0; color: #92400e;">
                    Đây là email TEST. Nếu bạn nhận được email này, hệ thống gửi email cho nhà cung cấp đã hoạt động HOÀN HẢO! ✅
                </p>
            </div>
        </div>

        <div class="footer">
            <strong style="color: #22c55e; font-size: 16px;">Green Grocery</strong><br>
            Hệ thống quản lý tạp hóa hiện đại<br>
            Email được gửi tự động từ hệ thống<br>
            <br>
            <em>Nếu nhận được email này, nghĩa là cấu hình email hoàn toàn chính xác!</em><br>
            © 2024 Green Grocery. All rights reserved.
        </div>
    </div>
</body>
</html>
    """
    
    # Plain text version
    text_content = """
ĐƠN ĐẶT HÀNG MỚI - TEST
Mã đơn: PO20241120TEST

=== THÔNG TIN ĐƠN HÀNG ===
Nhà cung cấp: Công ty bạn
Ngày tạo: 20/11/2024 14:30
Người tạo: Green Grocery Store
Ngày dự kiến giao: 25/11/2024

=== DANH SÁCH SẢN PHẨM (3 sản phẩm) ===
1. Coca Cola 330ml
   Số lượng: 50 thùng x 10,000đ = 500,000đ

2. Pepsi 330ml
   Số lượng: 30 thùng x 10,000đ = 300,000đ

3. Snack Oishi
   Số lượng: 100 gói x 5,000đ = 500,000đ

=== TỔNG KẾT ===
Tổng số lượng: 180 đơn vị
TỔNG GIÁ TRỊ: 1,300,000đ

Ghi chú: Đây là email TEST. Nếu bạn nhận được, hệ thống đã hoạt động HOÀN HẢO! ✅

---
Green Grocery
Hệ thống quản lý tạp hóa hiện đại
© 2024 Green Grocery
    """
    
    # Attach both versions
    part1 = MIMEText(text_content, 'plain', 'utf-8')
    part2 = MIMEText(html_content, 'html', 'utf-8')
    
    msg.attach(part1)
    msg.attach(part2)
    
    # Connect and send
    server = smtplib.SMTP(EMAIL_HOST, EMAIL_PORT, timeout=10)
    server.starttls()
    server.login(FROM_EMAIL, EMAIL_PASSWORD)
    server.send_message(msg)
    server.quit()
    
    print("=" * 70)
    print("✅✅✅ GỬI EMAIL THÀNH CÔNG! ✅✅✅")
    print("=" * 70)
    print(f"\n📬 Email đã được gửi:")
    print(f"   • Từ: {FROM_EMAIL} (Green Grocery)")
    print(f"   • Đến: {SUPPLIER_EMAIL} (Nhà cung cấp)")
    print(f"   • Subject: Đơn đặt hàng #PO20241120TEST")
    print(f"\n💡 YÊU CẦU NHÀ CUNG CẤP KIỂM TRA EMAIL:")
    print(f"   1. Mở email: {SUPPLIER_EMAIL}")
    print(f"   2. Tìm email từ 'Green Grocery'")
    print(f"   3. Subject: 'Đơn đặt hàng #PO20241120TEST'")
    print(f"   4. Nếu không thấy trong Inbox → Check Spam/Junk")
    print(f"\n🎉 HỆ THỐNG ĐÃ GỬI EMAIL ĐÚNG:")
    print(f"   • Từ email cấu hình: {FROM_EMAIL} ✅")
    print(f"   • Đến email nhà cung cấp: {SUPPLIER_EMAIL} ✅")
    
except Exception as e:
    print("=" * 70)
    print("❌ LỖI KHI GỬI EMAIL")
    print("=" * 70)
    print(f"Chi tiết: {str(e)}")
    print(f"\n💡 Kiểm tra:")
    print(f"   - Email nhà cung cấp đúng chưa: {SUPPLIER_EMAIL}")
    print(f"   - App Password còn hoạt động không")

print("\n" + "=" * 70)

