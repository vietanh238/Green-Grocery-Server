# 📧 Hướng dẫn cấu hình Email cho Purchase Order

## Tính năng
- ✅ Tự động gửi email cho nhà cung cấp khi tạo Purchase Order
- ✅ Email template HTML đẹp mắt, chuyên nghiệp
- ✅ Bao gồm đầy đủ thông tin đơn hàng, sản phẩm, giá trị
- ✅ API để gửi lại email nếu cần

## Cấu hình Email (Gmail)

### Bước 1: Tạo App Password cho Gmail

1. Đăng nhập Gmail của bạn
2. Vào **Google Account** → **Security**
3. Bật **2-Step Verification** (nếu chưa bật)
4. Vào **App passwords**
5. Chọn **Mail** và **Other (Custom name)**
6. Nhập tên: `Green Grocery`
7. Click **Generate**
8. Copy mã password (16 ký tự)

### Bước 2: Cập nhật settings.py

Mở `Server/Server/settings.py` và tìm phần Email Configuration:

```python
# Email Configuration
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = 'your-email@gmail.com'  # 👈 Thay bằng email của bạn
EMAIL_HOST_PASSWORD = 'your-app-password'  # 👈 Thay bằng App Password vừa tạo
DEFAULT_FROM_EMAIL = 'Green Grocery <noreply@green-grocery.io.vn>'
```

**Thay thế:**
- `your-email@gmail.com` → Email Gmail của bạn
- `your-app-password` → App Password 16 ký tự vừa copy

### Bước 3: Test Email

Sau khi cấu hình, test bằng cách:

1. Mở Products page
2. Click "Đặt hàng NCC"
3. Chọn nhà cung cấp (có email)
4. Tạo đơn đặt hàng
5. Kiểm tra email của nhà cung cấp

## Sử dụng Email Provider khác

### Outlook/Office 365

```python
EMAIL_HOST = 'smtp.office365.com'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = 'your-email@outlook.com'
EMAIL_HOST_PASSWORD = 'your-password'
```

### Custom SMTP Server

```python
EMAIL_HOST = 'smtp.your-domain.com'
EMAIL_PORT = 587  # hoặc 465 cho SSL
EMAIL_USE_TLS = True  # hoặc EMAIL_USE_SSL = True
EMAIL_HOST_USER = 'your-email@your-domain.com'
EMAIL_HOST_PASSWORD = 'your-password'
```

## Email Template

Email sẽ bao gồm:

### Header
- Logo/Title: "🛒 Đơn Đặt Hàng Mới"
- Mã đơn hàng

### Thông tin đơn hàng
- Tên nhà cung cấp
- Ngày tạo đơn
- Người tạo
- Ngày dự kiến giao hàng

### Danh sách sản phẩm
- Bảng chi tiết: STT, Tên SP, SKU, Số lượng, Đơn giá, Thành tiền
- Tổng số lượng
- Tổng giá trị đơn hàng

### Ghi chú
- Ghi chú thêm (nếu có)

### Footer
- Thông tin công ty
- Copyright

## APIs liên quan

### 1. Tạo Purchase Order (Auto-send email)
```
POST /api/purchase-order/create/
```

Response khi thành công:
```json
{
  "status": "1",
  "response": {
    "message": "Tạo đơn đặt hàng thành công và đã gửi email cho nhà cung cấp",
    "purchase_order": {...},
    "email_sent": true
  }
}
```

### 2. Gửi lại Email
```
POST /api/purchase-order/send-email/{po_id}/
```

Response:
```json
{
  "status": "1",
  "response": {
    "message": "Đã gửi email thành công đến supplier@example.com",
    "supplier_email": "supplier@example.com"
  }
}
```

## Troubleshooting

### Email không được gửi?

1. **Check email configuration:**
   ```bash
   # Django shell
   python manage.py shell
   >>> from django.core.mail import send_mail
   >>> send_mail('Test', 'Test email', 'from@example.com', ['to@example.com'])
   ```

2. **Kiểm tra App Password Gmail:**
   - Đảm bảo 2-Step Verification đã bật
   - App Password phải là 16 ký tự
   - Không có khoảng trắng

3. **Kiểm tra firewall/network:**
   - Port 587 (TLS) hoặc 465 (SSL) phải open
   - Không bị chặn bởi firewall

4. **Check logs:**
   ```bash
   tail -f logs/django.log
   ```

### Email bị vào Spam?

- Thêm SPF record cho domain
- Sử dụng DKIM signing
- Có thể dùng email service chuyên nghiệp (SendGrid, AWS SES, Mailgun)

## Security Best Practices

### 1. Sử dụng Environment Variables

Thay vì hardcode trong settings.py:

```python
# .env file
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-password

# settings.py
import os
from decouple import config

EMAIL_HOST_USER = config('EMAIL_HOST_USER')
EMAIL_HOST_PASSWORD = config('EMAIL_HOST_PASSWORD')
```

### 2. NEVER commit email credentials
Thêm vào `.gitignore`:
```
.env
*.env
```

## Production Recommendations

Cho môi trường production, nên sử dụng:

1. **AWS SES** (Amazon Simple Email Service)
2. **SendGrid**
3. **Mailgun**
4. **SMTP relay service**

Thay vì Gmail để:
- ✅ Không bị giới hạn số email/ngày
- ✅ Tốc độ gửi nhanh hơn
- ✅ Tracking & Analytics
- ✅ Better deliverability

---

## 🎉 Hoàn tất!

Sau khi cấu hình xong, mỗi khi tạo đơn đặt hàng, nhà cung cấp sẽ tự động nhận email đẹp mắt với đầy đủ thông tin!

