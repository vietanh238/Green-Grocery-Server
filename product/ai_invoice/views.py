from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from django.db.models import Q
from core.models import Product
from io import BytesIO
import os
import re

try:
    from PIL import Image
    import pytesseract

    tesseract_paths = [
        r"C:\Program Files\Tesseract-OCR\tesseract.exe",
        r"C:\Program Files (x86)\Tesseract-OCR\tesseract.exe",
        r"C:\Tesseract-OCR\tesseract.exe",
    ]

    tesseract_found = False
    for path in tesseract_paths:
        if os.path.exists(path):
            pytesseract.pytesseract.tesseract_cmd = path
            tesseract_found = True
            break

    if not tesseract_found:
        try:
            pytesseract.get_tesseract_version()
        except Exception:
            pytesseract = None
except Exception:
    Image = None
    pytesseract = None


class ParseProductInvoiceImageView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        try:
            invoice_file = request.FILES.get("file")
            if not invoice_file:
                return Response(
                    {
                        "status": "2",
                        "response": {
                            "error_code": "001",
                            "error_message_us": "Missing file",
                            "error_message_vn": "Vui lòng chọn file hóa đơn",
                        },
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )

            if Image is None or pytesseract is None:
                return Response(
                    {
                        "status": "2",
                        "response": {
                            "error_code": "002",
                            "error_message_us": "OCR engine not configured",
                            "error_message_vn": "Máy chủ chưa được cấu hình OCR để đọc ảnh hóa đơn",
                            "suggestion": "Vui lòng cài đặt Tesseract OCR:\n1. Tải từ: https://github.com/UB-Mannheim/tesseract/wiki\n2. Cài đặt vào đường dẫn mặc định: C:\\Program Files\\Tesseract-OCR\\\n3. Khởi động lại server Django",
                        },
                    },
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR,
                )

            try:
                image_bytes = invoice_file.read()
                image = Image.open(BytesIO(image_bytes))

                if image.mode != 'RGB':
                    image = image.convert('RGB')
            except Exception as img_error:
                return Response(
                    {
                        "status": "2",
                        "response": {
                            "error_code": "003",
                            "error_message_us": "Invalid image file",
                            "error_message_vn": f"File không phải là hình ảnh hợp lệ: {str(img_error)}",
                        },
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )

            try:
                ocr_text = pytesseract.image_to_string(image, lang="vie+eng")
            except Exception as ocr_error:
                error_msg = str(ocr_error)
                if "tesseract is not installed" in error_msg.lower() or "not in your path" in error_msg.lower():
                    return Response(
                        {
                            "status": "2",
                            "response": {
                                "error_code": "002",
                                "error_message_us": "Tesseract not found",
                                "error_message_vn": "Không tìm thấy Tesseract OCR. Vui lòng cài đặt Tesseract OCR.",
                                "suggestion": "Hướng dẫn cài đặt:\n1. Tải Tesseract từ: https://github.com/UB-Mannheim/tesseract/wiki\n2. Cài đặt vào: C:\\Program Files\\Tesseract-OCR\\\n3. Khởi động lại server Django\n\nHoàn toàn MIỄN PHÍ, chỉ cần cài 1 lần!",
                            },
                        },
                        status=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    )
                raise

            if not ocr_text or not ocr_text.strip():
                return Response(
                    {
                        "status": "2",
                        "response": {
                            "error_code": "004",
                            "error_message_us": "Cannot read invoice",
                            "error_message_vn": "Không đọc được nội dung hóa đơn, vui lòng thử lại với ảnh rõ nét hơn",
                        },
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )

            lines = [line.strip() for line in ocr_text.splitlines() if line.strip()]
            products = []
            debug_info = []
            raw_ocr_lines = lines[:20]

            product_qs = Product.objects.filter(created_by=request.user, is_active=True)
            all_products = list(product_qs)

            if not all_products:
                return Response(
                    {
                        "status": "2",
                        "response": {
                            "error_code": "006",
                            "error_message_us": "No products in database",
                            "error_message_vn": "Chưa có sản phẩm nào trong hệ thống. Vui lòng thêm sản phẩm trước khi sử dụng chức năng này.",
                        },
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )

            stop_words = {
                'tap', 'hoa', 'anh', 'khang', 'duong', 'le', 'loi', 'quan', 'tphcm',
                'ngay', 'tong', 'tien', 'cong', 'san', 'pham', 'sku', 'barcode',
                'phan', 'loai', 'gia', 'nhap', 'ban', 'so', 'luong', 'don', 'vi',
                'stt', 'ten', 'hang', 'hoa', 'don', 'thanh', 'toan', 'vnd', 'dong'
            }

            for line_idx, line in enumerate(lines):
                if len(line) < 5:
                    continue

                parts = [p.strip() for p in line.split() if p.strip()]
                if len(parts) < 2:
                    continue

                quantity = None
                unit_price = None
                barcode = None
                total_price = None

                numeric_values = []
                text_parts = []

                for p in parts:
                    cleaned = (
                        p.replace(".", "")
                        .replace(",", "")
                        .replace("đ", "")
                        .replace("VND", "")
                        .replace("vnd", "")
                        .replace("₫", "")
                        .strip()
                    )

                    if cleaned.isdigit():
                        num_val = int(cleaned)
                        cleaned_len = len(cleaned)

                        if cleaned_len in (12, 13):
                            barcode = cleaned
                        elif num_val > 0:
                            numeric_values.append((num_val, cleaned_len))
                    else:
                        p_lower = p.lower()
                        if p_lower not in stop_words and len(p) > 1:
                            text_parts.append(p)

                if not numeric_values:
                    continue

                numeric_values.sort(key=lambda x: x[1], reverse=True)

                if len(numeric_values) >= 1:
                    quantity = numeric_values[0][0]
                if len(numeric_values) >= 2:
                    unit_price = numeric_values[1][0]
                if len(numeric_values) >= 3:
                    total_price = numeric_values[2][0]

                if not quantity or quantity <= 0:
                    continue

                if unit_price and unit_price <= 0:
                    unit_price = None

                if total_price and unit_price and abs(total_price - (quantity * unit_price)) > (quantity * unit_price * 0.1):
                    total_price = None

                product_name_candidate = " ".join(text_parts).strip() if text_parts else ""

                if not product_name_candidate or len(product_name_candidate) < 2:
                    continue

                product = None
                match_method = None
                match_score = 0

                if barcode:
                    product = product_qs.filter(bar_code=barcode).first()
                    if product:
                        match_method = "barcode"
                        match_score = 100

                if not product and product_name_candidate:
                    product_name_lower = product_name_candidate.lower()
                    best_match = None
                    best_score = 0

                    for p in all_products:
                        p_name_lower = p.name.lower()
                        score = 0

                        if product_name_lower == p_name_lower:
                            score = 100
                        elif product_name_lower in p_name_lower:
                            score = 80
                        elif p_name_lower in product_name_lower:
                            score = 70
                        else:
                            p_words = set(p_name_lower.split())
                            line_words = set(product_name_lower.split())
                            common_words = p_words.intersection(line_words)

                            if len(common_words) >= 3:
                                score = 60
                            elif len(common_words) >= 2:
                                score = 40

                        if score > best_score:
                            best_score = score
                            best_match = p

                    if best_match and best_score >= 40:
                        product = best_match
                        match_method = "name_match"
                        match_score = best_score

                if not product:
                    debug_info.append({
                        "line": line_idx + 1,
                        "text": product_name_candidate,
                        "quantity": quantity,
                        "unit_price": unit_price,
                        "barcode": barcode
                    })
                    continue

                try:
                    cost_price = float(unit_price) if unit_price is not None and unit_price > 0 else float(product.cost_price)
                    selling_price = float(product.price)

                    if cost_price <= 0:
                        cost_price = float(product.cost_price)

                    if selling_price <= 0:
                        selling_price = cost_price * 1.2

                    products.append({
                        "name": product.name,
                        "sku": product.sku,
                        "barCode": product.bar_code,
                        "category": product.category.name if product.category else "",
                        "costPrice": round(cost_price, 2),
                        "price": round(selling_price, 2),
                        "quantity": int(quantity),
                        "unit": product.unit,
                        "reorderPoint": int(product.reorder_point),
                        "maxStockLevel": int(product.max_stock_level),
                        "supplierName": product.supplier.name if product.supplier else "",
                        "hasExpiry": bool(product.has_expiry),
                        "shelfLifeDays": product.shelf_life_days,
                    })
                except (ValueError, TypeError, AttributeError) as e:
                    debug_info.append({
                        "line": line_idx + 1,
                        "text": product_name_candidate,
                        "error": f"Lỗi xử lý dữ liệu: {str(e)}"
                    })
                    continue

            if not products:
                unmatched_samples = [d.get("text", "N/A") for d in debug_info[:10]]
                return Response(
                    {
                        "status": "2",
                        "response": {
                            "error_code": "005",
                            "error_message_us": "No line items detected",
                            "error_message_vn": "Không tìm thấy dòng hàng nào hợp lệ trong hóa đơn",
                            "debug_info": {
                                "ocr_lines_sample": raw_ocr_lines[:10],
                                "unmatched_items": unmatched_samples,
                                "total_products_in_db": len(all_products),
                                "sample_product_names": [p.name for p in all_products[:10]],
                            },
                            "suggestion": "Vui lòng kiểm tra:\n1. Tên sản phẩm trong hóa đơn có khớp với tên sản phẩm trong hệ thống không?\n2. Đảm bảo ảnh hóa đơn rõ nét, không bị mờ\n3. Format hóa đơn: Tên sản phẩm - Số lượng - Đơn giá\n4. Đảm bảo sản phẩm đã tồn tại trong hệ thống\n\nGợi ý: Nếu đây là bảng Excel, vui lòng dùng chức năng 'Tải file mẫu Excel' thay vì đọc ảnh.",
                        },
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )

            return Response(
                {
                    "status": "1",
                    "response": {
                        "products": products,
                        "raw_text": ocr_text[:500],
                        "matched_count": len(products),
                        "total_lines_processed": len(lines)
                    },
                },
                status=status.HTTP_200_OK,
            )

        except Exception as exc:
            import traceback
            error_trace = traceback.format_exc()
            return Response(
                {
                    "status": "2",
                    "response": {
                        "error_code": "9999",
                        "error_message_us": "System error",
                        "error_message_vn": f"Lỗi hệ thống: {str(exc)}",
                        "debug_trace": error_trace if request.user.is_staff else None,
                    },
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
