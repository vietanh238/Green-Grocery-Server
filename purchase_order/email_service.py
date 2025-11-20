from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.conf import settings
from datetime import datetime


class PurchaseOrderEmailService:
    """Service to send purchase order emails to suppliers"""

    @staticmethod
    def send_purchase_order_email(purchase_order):
        """
        Send purchase order email to supplier

        Args:
            purchase_order: PurchaseOrder instance

        Returns:
            bool: True if email sent successfully, False otherwise
        """
        try:
            supplier = purchase_order.supplier

            # Check if supplier has email
            if not supplier.email:
                return False

            # Prepare email data
            context = {
                'po_code': purchase_order.po_code,
                'supplier_name': supplier.name,
                'supplier_code': supplier.supplier_code,
                'total_amount': purchase_order.total_amount,
                'expected_date': purchase_order.expected_date,
                'created_at': purchase_order.created_at,
                'created_by': purchase_order.created_by.last_name if purchase_order.created_by else 'N/A',
                'items': [],
                'note': purchase_order.note or '',
                'current_year': datetime.now().year,
            }

            # Add items
            total_quantity = 0
            for item in purchase_order.items.all():
                context['items'].append({
                    'product_name': item.product.name if item.product else 'N/A',
                    'product_sku': item.product.sku if item.product else 'N/A',
                    'quantity': item.quantity,
                    'unit': item.product.unit if item.product else '',
                    'unit_price': item.unit_price,
                    'total_price': item.total_price,
                })
                total_quantity += item.quantity

            context['total_quantity'] = total_quantity
            context['items_count'] = len(context['items'])

            # Create email subject
            subject = f'Đơn đặt hàng #{purchase_order.po_code} - Green Grocery'

            # Render HTML email template
            html_content = PurchaseOrderEmailService._render_html_template(context)

            # Create plain text version
            text_content = PurchaseOrderEmailService._render_text_template(context)

            # Create email
            email = EmailMultiAlternatives(
                subject=subject,
                body=text_content,
                from_email=settings.DEFAULT_FROM_EMAIL,
                to=[supplier.email],
            )

            # Attach HTML version
            email.attach_alternative(html_content, "text/html")

            # Send email
            email.send()

            return True

        except Exception as e:
            print(f"Error sending PO email: {str(e)}")
            return False

    @staticmethod
    def _render_html_template(context):
        """Render HTML email template"""
        html_template = """
<!DOCTYPE html>
<html lang="vi">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Đơn đặt hàng</title>
    <style>
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
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
            font-weight: 700;
        }
        .header .po-code {
            font-size: 18px;
            margin-top: 10px;
            opacity: 0.95;
        }
        .content {
            padding: 30px;
        }
        .info-section {
            margin-bottom: 30px;
        }
        .info-section h2 {
            color: #22c55e;
            font-size: 18px;
            margin-bottom: 15px;
            border-bottom: 2px solid #22c55e;
            padding-bottom: 8px;
        }
        .info-grid {
            display: grid;
            grid-template-columns: 140px 1fr;
            gap: 12px;
            background: #f9fafb;
            padding: 20px;
            border-radius: 8px;
        }
        .info-label {
            font-weight: 600;
            color: #6b7280;
        }
        .info-value {
            color: #1a1a1a;
        }
        .items-table {
            width: 100%;
            border-collapse: collapse;
            margin-top: 15px;
            border: 1px solid #e5e7eb;
            border-radius: 8px;
            overflow: hidden;
        }
        .items-table thead {
            background: #f9fafb;
        }
        .items-table th {
            padding: 12px;
            text-align: left;
            font-weight: 600;
            color: #374151;
            font-size: 13px;
            text-transform: uppercase;
            border-bottom: 2px solid #e5e7eb;
        }
        .items-table td {
            padding: 12px;
            border-bottom: 1px solid #f3f4f6;
        }
        .items-table tr:last-child td {
            border-bottom: none;
        }
        .items-table tr:hover {
            background: #f9fafb;
        }
        .text-right {
            text-align: right;
        }
        .text-center {
            text-align: center;
        }
        .summary {
            background: linear-gradient(135deg, #f0fdf4, #dcfce7);
            padding: 20px;
            border-radius: 8px;
            margin-top: 20px;
            border: 2px solid #22c55e;
        }
        .summary-row {
            display: flex;
            justify-content: space-between;
            padding: 8px 0;
        }
        .summary-row.total {
            border-top: 2px solid #22c55e;
            margin-top: 10px;
            padding-top: 15px;
            font-size: 18px;
            font-weight: 700;
            color: #22c55e;
        }
        .note-section {
            background: #fffbeb;
            border-left: 4px solid #f59e0b;
            padding: 15px;
            margin-top: 20px;
            border-radius: 4px;
        }
        .note-section h3 {
            margin: 0 0 8px 0;
            color: #f59e0b;
            font-size: 14px;
        }
        .footer {
            background: #f9fafb;
            padding: 25px;
            text-align: center;
            color: #6b7280;
            font-size: 13px;
            border-top: 1px solid #e5e7eb;
        }
        .footer strong {
            color: #22c55e;
            font-size: 16px;
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
            <div class="po-code">Mã đơn: <strong>{{ po_code }}</strong></div>
        </div>

        <div class="content">
            <div class="info-section">
                <h2>📋 Thông tin đơn hàng</h2>
                <div class="info-grid">
                    <div class="info-label">Nhà cung cấp:</div>
                    <div class="info-value"><strong>{{ supplier_name }}</strong> ({{ supplier_code }})</div>

                    <div class="info-label">Ngày tạo đơn:</div>
                    <div class="info-value">{{ created_at|date:"d/m/Y H:i" }}</div>

                    <div class="info-label">Người tạo:</div>
                    <div class="info-value">{{ created_by }}</div>

                    <div class="info-label">Ngày dự kiến:</div>
                    <div class="info-value"><strong>{{ expected_date|date:"d/m/Y" }}</strong> <span class="badge">Cần giao trước ngày này</span></div>
                </div>
            </div>

            <div class="info-section">
                <h2>📦 Danh sách sản phẩm ({{ items_count }} sản phẩm)</h2>
                <table class="items-table">
                    <thead>
                        <tr>
                            <th style="width: 50px;" class="text-center">#</th>
                            <th>Sản phẩm</th>
                            <th style="width: 100px;">SKU</th>
                            <th style="width: 100px;" class="text-center">Số lượng</th>
                            <th style="width: 120px;" class="text-right">Đơn giá</th>
                            <th style="width: 130px;" class="text-right">Thành tiền</th>
                        </tr>
                    </thead>
                    <tbody>
                        {% for item in items %}
                        <tr>
                            <td class="text-center">{{ forloop.counter }}</td>
                            <td><strong>{{ item.product_name }}</strong></td>
                            <td>{{ item.product_sku }}</td>
                            <td class="text-center"><strong>{{ item.quantity }}</strong> {{ item.unit }}</td>
                            <td class="text-right">{{ item.unit_price|floatformat:0 }}đ</td>
                            <td class="text-right"><strong>{{ item.total_price|floatformat:0 }}đ</strong></td>
                        </tr>
                        {% endfor %}
                    </tbody>
                </table>

                <div class="summary">
                    <div class="summary-row">
                        <span>Tổng số lượng:</span>
                        <strong>{{ total_quantity }} đơn vị</strong>
                    </div>
                    <div class="summary-row total">
                        <span>TỔNG GIÁ TRỊ ĐơN HÀNG:</span>
                        <span>{{ total_amount|floatformat:0 }}đ</span>
                    </div>
                </div>
            </div>

            {% if note %}
            <div class="note-section">
                <h3>📝 Ghi chú:</h3>
                <p style="margin: 0; color: #92400e;">{{ note }}</p>
            </div>
            {% endif %}
        </div>

        <div class="footer">
            <strong>Green Grocery</strong><br>
            Hệ thống quản lý tạp hóa hiện đại<br>
            Email được gửi tự động từ hệ thống<br>
            © {{ current_year }} Green Grocery. All rights reserved.
        </div>
    </div>
</body>
</html>
        """

        from django.template import Template, Context
        template = Template(html_template)
        return template.render(Context(context))

    @staticmethod
    def _render_text_template(context):
        """Render plain text email template"""
        text = f"""
ĐƠN ĐẶT HÀNG MỚI
Mã đơn: {context['po_code']}

=== THÔNG TIN ĐƠN HÀNG ===
Nhà cung cấp: {context['supplier_name']} ({context['supplier_code']})
Ngày tạo: {context['created_at'].strftime('%d/%m/%Y %H:%M')}
Người tạo: {context['created_by']}
Ngày dự kiến giao: {context['expected_date'].strftime('%d/%m/%Y')}

=== DANH SÁCH SẢN PHẨM ({context['items_count']} sản phẩm) ===
"""
        for idx, item in enumerate(context['items'], 1):
            text += f"{idx}. {item['product_name']} ({item['product_sku']})\n"
            text += f"   Số lượng: {item['quantity']} {item['unit']} x {item['unit_price']:,.0f}đ = {item['total_price']:,.0f}đ\n\n"

        text += f"""
=== TỔNG KẾT ===
Tổng số lượng: {context['total_quantity']} đơn vị
TỔNG GIÁ TRỊ: {context['total_amount']:,.0f}đ
"""

        if context['note']:
            text += f"\nGhi chú: {context['note']}\n"

        text += f"""
---
Green Grocery
Hệ thống quản lý tạp hóa hiện đại
© {context['current_year']} Green Grocery
        """

        return text


