from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from django.db.models import Q, Sum, Count, Prefetch
from datetime import datetime, timedelta
from decimal import Decimal
from core.models import Order, Payment, OrderItem


class TransactionHistoryView(APIView):
    """
    API để lấy lịch sử giao dịch (đơn hàng gần đây)
    Hỗ trợ filter theo: date, type, status, payment_method
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            user = request.user

            # Parse query parameters
            date_from = request.query_params.get('date_from')
            date_to = request.query_params.get('date_to')
            transaction_type = request.query_params.get('type')
            transaction_status = request.query_params.get('status')
            payment_method_filter = request.query_params.get('payment_method')

            # Set default date range (30 days)
            if not date_from:
                date_from = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')
            if not date_to:
                date_to = datetime.now().strftime('%Y-%m-%d')

            transactions = []

            # Get sales transactions (Orders)
            sales_query = self._get_sales_transactions(user, date_from, date_to)
            if not transaction_type or transaction_type == 'sale':
                for order in sales_query:
                    # Map Order status to transaction status
                    trans_status = self._map_order_status(order.status)

                    # Map to payment method
                    trans_payment_method = self._map_payment_method(order)

                    transactions.append({
                        'id': str(order.id),
                        'type': 'sale',
                        'order_code': order.order_code,
                        'created_at': order.created_at.isoformat(),
                        'customer_name': order.buyer_name if order.buyer_name else 'Khách lẻ',
                        'amount': float(order.total_amount) if order.total_amount else 0.0,
                        'payment_method': trans_payment_method,
                        'status': trans_status,
                        'note': order.note if order.note else '',
                        'items_count': order.items.count() if hasattr(order, 'items') else 0,
                    })

            # Get import transactions (PurchaseOrders) - Currently empty
            imports_query = self._get_import_transactions(user, date_from, date_to)
            if not transaction_type or transaction_type == 'import':
                for import_record in imports_query:
                    supplier_name = 'Nhà cung cấp'
                    if hasattr(import_record, 'supplier') and import_record.supplier:
                        supplier_name = import_record.supplier.name

                    transactions.append({
                        'id': str(import_record.id),
                        'type': 'import',
                        'order_code': import_record.po_code if hasattr(import_record, 'po_code') else f'IMP-{import_record.id}',
                        'created_at': import_record.created_at.isoformat(),
                        'customer_name': supplier_name,
                        'amount': float(import_record.total_amount) if hasattr(import_record, 'total_amount') else 0.0,
                        'payment_method': 'cash',
                        'status': 'completed',
                        'note': import_record.note if hasattr(import_record, 'note') and import_record.note else '',
                    })

            # Get payment transactions (Payments)
            payment_query = self._get_payment_transactions(user, date_from, date_to)
            if not transaction_type or transaction_type == 'payment':
                for payment in payment_query:
                    # Get customer name from related order
                    customer_name = 'Khách lẻ'
                    if payment.order and payment.order.buyer_name:
                        customer_name = payment.order.buyer_name

                    transactions.append({
                        'id': str(payment.id),
                        'type': 'payment',
                        'order_code': payment.order.order_code if payment.order else f'PAY-{payment.id}',
                        'created_at': payment.created_at.isoformat(),
                        'customer_name': customer_name,
                        'amount': float(payment.paid_amount) if payment.paid_amount else 0.0,
                        'payment_method': payment.payment_method if payment.payment_method else 'cash',
                        'status': self._map_payment_status(payment.status),
                        'note': payment.description if payment.description else '',
                    })

            # Apply filters
            if transaction_status:
                transactions = [t for t in transactions if t['status'] == transaction_status]

            if payment_method_filter:
                transactions = [t for t in transactions if t['payment_method'] == payment_method_filter]

            # Sort by created_at (newest first)
            transactions.sort(key=lambda x: x['created_at'], reverse=True)

            # Calculate statistics
            stats = self._calculate_stats(transactions)

            return Response({
                'status': '1',
                'response': {
                    'transactions': transactions,
                    'stats': stats,
                    'filters': {
                        'date_from': date_from,
                        'date_to': date_to,
                        'type': transaction_type,
                        'status': transaction_status,
                        'payment_method': payment_method_filter,
                    }
                }
            }, status=status.HTTP_200_OK)

        except Exception as ex:
            import traceback
            traceback.print_exc()
            return Response({
                'status': '2',
                'response': {
                    'error_code': '9999',
                    'error_message_us': 'An internal server error occurred.',
                    'error_message_vn': f'Lỗi hệ thống: {str(ex)}'
                }
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def _get_sales_transactions(self, user, date_from, date_to):
        """Get all orders (sales) for the user within date range"""
        return Order.objects.filter(
            user=user,
            created_at__date__gte=date_from,
            created_at__date__lte=date_to,
            is_active=True
        ).select_related('customer').prefetch_related('items').order_by('-created_at')

    def _get_import_transactions(self, user, date_from, date_to):
        """Get all import/purchase orders - Currently returns empty"""
        # TODO: Implement when PurchaseOrder is used for imports
        return []

    def _get_payment_transactions(self, user, date_from, date_to):
        """Get all payments for the user within date range"""
        return Payment.objects.filter(
            created_by=user,
            created_at__date__gte=date_from,
            created_at__date__lte=date_to,
            is_active=True
        ).select_related('order').order_by('-created_at')

    def _map_order_status(self, order_status):
        """Map Order status to transaction status"""
        status_mapping = {
            'paid': 'completed',
            'pending': 'pending',
            'failed': 'cancelled',
            'cancelled': 'cancelled',
            'refunded': 'cancelled',
        }
        return status_mapping.get(order_status, 'pending')

    def _map_payment_status(self, payment_status):
        """Map Payment status to transaction status"""
        status_mapping = {
            'paid': 'completed',
            'pending': 'pending',
            'cancelled': 'cancelled',
            'failed': 'cancelled',
        }
        return status_mapping.get(payment_status, 'pending')

    def _map_payment_method(self, order):
        """Map Order payment_method or status to transaction payment method"""
        if hasattr(order, 'payment_method') and order.payment_method:
            return order.payment_method

        # Fallback: infer from status
        if order.status == 'paid':
            return 'qr'
        elif order.status == 'pending':
            return 'debt'
        else:
            return 'cash'

    def _calculate_stats(self, transactions):
        """Calculate transaction statistics"""
        total_sales = sum(1 for t in transactions if t['type'] == 'sale')
        total_imports = sum(1 for t in transactions if t['type'] == 'import')
        total_payments = sum(1 for t in transactions if t['type'] == 'payment')
        total_refunds = sum(1 for t in transactions if t['type'] == 'refund')

        # Calculate revenue (sales + payments)
        period_revenue = sum(
            t['amount'] for t in transactions
            if t['type'] in ['sale', 'payment'] and t['status'] == 'completed'
        )

        # Calculate expenses (imports)
        period_expenses = sum(
            t['amount'] for t in transactions
            if t['type'] == 'import' and t['status'] == 'completed'
        )

        net_amount = period_revenue - period_expenses

        return {
            'total_sales': total_sales,
            'total_imports': total_imports,
            'total_payments': total_payments,
            'total_refunds': total_refunds,
            'total_transactions': len(transactions),
            'period_revenue': float(period_revenue),
            'period_expenses': float(period_expenses),
            'net_amount': float(net_amount),
        }
