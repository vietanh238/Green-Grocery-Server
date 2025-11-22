# PayOS Payment Integration Setup

## 🔑 Required Environment Variables

Để sử dụng tính năng thanh toán QR code với PayOS, bạn cần cấu hình các biến môi trường sau trong file `.env`:

```env
# PayOS Credentials
PAYOS_CLIENT_ID=your_client_id_here
PAYOS_API_KEY=your_api_key_here
PAYOS_CHECKSUM_KEY=your_checksum_key_here
```

## 📝 Cách lấy PayOS Credentials

1. **Đăng ký tài khoản PayOS:**
   - Truy cập: https://payos.vn/
   - Đăng ký tài khoản doanh nghiệp

2. **Lấy API Keys:**
   - Đăng nhập vào Dashboard PayOS
   - Vào mục **Settings** → **API Keys**
   - Copy các thông tin:
     - `Client ID`
     - `API Key`
     - `Checksum Key`

3. **Cập nhật file `.env`:**
   ```bash
   cd Server
   nano .env  # hoặc dùng text editor khác
   ```

4. **Restart server:**
   ```bash
   python manage.py runserver
   ```

## 🧪 Test PayOS Integration

### 1. Check PayOS Connection
```bash
# Trong terminal, test PayOS API
curl -X POST https://api-merchant.payos.vn/v2/payment-requests \
  -H "x-client-id: YOUR_CLIENT_ID" \
  -H "x-api-key: YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "orderCode": 123456,
    "amount": 10000,
    "description": "Test payment",
    "returnUrl": "https://example.com/success",
    "cancelUrl": "https://example.com/cancel",
    "signature": "YOUR_SIGNATURE"
  }'
```

### 2. Expected Response Format
```json
{
  "code": "00",
  "desc": "Success",
  "data": {
    "paymentLinkId": "abc123",
    "checkoutUrl": "https://pay.payos.vn/...",
    "qrCode": "https://qr.payos.vn/..."
  }
}
```

### 3. Common Errors

#### ❌ Error: "orderCode must be a number conforming to the specified constraints"
**Nguyên nhân:** `orderCode` quá lớn hoặc không đúng định dạng

**Giải pháp:**
- `orderCode` phải là số nguyên dương (integer)
- `orderCode` không được vượt quá 9007199254740991 (JavaScript MAX_SAFE_INTEGER)
- Khuyến nghị: Sử dụng orderCode trong khoảng 100000000-999999999 (9 digits)
- **ĐÃ FIX:** Frontend tạo orderCode từ timestamp với modulo để đảm bảo 9 digits

#### ❌ Error: "PayOS did not return QR code"
**Nguyên nhân:** API PayOS không trả về `qrCode` hoặc `checkoutUrl`

**Giải pháp:**
- Kiểm tra API keys có đúng không
- Kiểm tra tài khoản PayOS đã được kích hoạt chưa
- Kiểm tra `amount` phải >= 2000 VND (yêu cầu của PayOS)
- Kiểm tra signature generation có đúng không
- Kiểm tra orderCode có đúng định dạng không (xem lỗi trên)

#### ❌ Error: "Invalid checksum"
**Nguyên nhân:** `PAYOS_CHECKSUM_KEY` không đúng hoặc signature generation sai

**Giải pháp:**
- Copy lại Checksum Key từ PayOS Dashboard
- Đảm bảo không có space thừa trong `.env`

#### ❌ Error: "401 Unauthorized"
**Nguyên nhân:** `PAYOS_CLIENT_ID` hoặc `PAYOS_API_KEY` không đúng

**Giải pháp:**
- Kiểm tra lại credentials từ PayOS Dashboard
- Đảm bảo account PayOS đã được xác thực

## 🔄 Changes Made to Fix QR Code Issue

### Backend Changes (`Server/payments/payment/views.py`)
```python
# ❌ BEFORE: Always showed fallback VietQR even if PayOS failed
if not qr_code:
    # Generate VietQR fallback
    qr_code = f"https://img.vietqr.io/..."

# ✅ AFTER: Return error if PayOS doesn't provide QR code
if not qr_code or not checkout_url:
    order.delete()
    return Response({
        'status': '2',
        'response': {
            'error_code': '004',
            'error_message_vn': 'Không thể tạo mã QR thanh toán. Vui lòng thử lại sau.'
        }
    }, status=status.HTTP_502_BAD_GATEWAY)
```

### Frontend Changes (`Client/src/app/component/qrpay/qrpay.component.ts`)
```typescript
// ✅ Check if QR code exists, close dialog if not
if (!rs.response.qrCode) {
  this.showError('Không thể tạo mã QR. Vui lòng thử lại sau.');
  setTimeout(() => {
    this.dialogRef.close({ cancel: true, error: 'No QR code' });
  }, 2000);
  return;
}
```

## 📊 Debug Logs

Khi có vấn đề với PayOS, check logs trong terminal:

```bash
# PayOS Request logs
🔵 PayOS Request URL: https://api-merchant.payos.vn/v2/payment-requests
🔵 PayOS Request Body: {...}

# Success logs
✅ PayOS Response: {"code":"00","data":{...}}

# Error logs
❌ PayOS HTTP Error: 401 Unauthorized
❌ PayOS Response: {"code":"01","desc":"Invalid credentials"}
```

## 🆘 Support

Nếu vẫn gặp vấn đề:
1. Check PayOS Dashboard: https://my.payos.vn/
2. PayOS Documentation: https://payos.vn/docs/
3. PayOS Support: support@payos.vn

## ✅ Checklist

- [ ] Đã có tài khoản PayOS
- [ ] Đã lấy được API credentials
- [ ] Đã cập nhật file `.env`
- [ ] Đã restart Django server
- [ ] Test tạo payment thành công
- [ ] QR code hiển thị đúng
- [ ] Webhook hoạt động (nếu có)

