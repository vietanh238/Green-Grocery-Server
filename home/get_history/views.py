from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from django.db.models import Q, Sum, Count
from datetime import datetime, timedelta
from decimal import Decimal


class TransactionHistoryView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            user = request.user
            date_from = request.query_params.get('date_from')
            date_to = request.query_params.get('date_to')
            transaction_type = request.query_params.get('type')
            transaction_status = request.query_params.get('status')
            payment_method = request.query_params.get('payment_method')

            if not date_from:
                date_from = (datetime.now() - timedelta(days=30)
                             ).strftime('%Y-%m-%d')
            if not date_to:
                date_to = datetime.now().strftime('%Y-%m-%d')

            transactions = []

            sales_query = self._get_sales_transactions(
                user, date_from, date_to)
            if not transaction_type or transaction_type == 'sale':
                for sale in sales_query:
                    transactions.append({
                        'id': str(sale.id),
                        'type': 'sale',
                        'order_code': sale.order_code,
                        'created_at': sale.created_at.isoformat(),
                        'customer_name': sale.buyer_name if sale.buyer_name else 'Khách lẻ',
                        'amount': float(sale.total_amount),
                        'payment_method': self._get_payment_method(sale.status),
                        'status': sale.status,
                        'note': sale.note if hasattr(sale, 'note') else '',
                    })

            imports_query = self._get_import_transactions(
                user, date_from, date_to)
            if not transaction_type or transaction_type == 'import':
                for import_record in imports_query:
                    transactions.append({
                        'id': str(import_record.id),
                        'type': 'import',
                        'order_code': f'IMP-{import_record.id}',
                        'created_at': import_record.created_at.isoformat(),
                        'customer_name': import_record.supplier_name if hasattr(import_record, 'supplier_name') else 'Nhà cung cấp',
                        'amount': float(import_record.total_cost),
                        'payment_method': 'cash',
                        'status': 'completed',
                        'note': import_record.note if hasattr(import_record, 'note') else '',
                    })

            payment_query = self._get_payment_transactions(
                user, date_from, date_to)
            if not transaction_type or transaction_type == 'payment':
                for payment in payment_query:
                    transactions.append({
                        'id': str(payment.id),
                        'type': 'payment',
                        'order_code': payment.payment_code if hasattr(payment, 'payment_code') else f'PAY-{payment.id}',
                        'created_at': payment.created_at.isoformat(),
                        'customer_name': payment.customer_name if hasattr(payment, 'customer_name') else 'Thanh toán công nợ',
                        'amount': float(payment.paid_amount),
                        'payment_method': payment.payment_method if hasattr(payment, 'payment_method') else 'cash',
                        'status': 'completed',
                        'note': payment.note if hasattr(payment, 'note') else '',
                    })

            if transaction_status:
                transactions = [
                    t for t in transactions if t['status'] == transaction_status]

            if payment_method:
                transactions = [
                    t for t in transactions if t['payment_method'] == payment_method]

            transactions.sort(key=lambda x: x['created_at'], reverse=True)

            stats = self._calculate_stats(
                transactions, sales_query, imports_query, payment_query)

            return Response({
                'status': '1',
                'response': {
                    'transactions': transactions,
                    'stats': stats
                }
            }, status=status.HTTP_200_OK)

        except Exception as ex:
            return Response({
                'status': '2',
                'response': {
                    'error_code': '9999',
                    'error_message_us': 'An internal server error occurred.',
                    'error_message_vn': f'Lỗi hệ thống: {str(ex)}'
                }
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def _get_sales_transactions(self, user, date_from, date_to):
        from orders.models import Order

        return Order.objects.filter(
            user=user,
            created_at__date__gte=date_from,
            created_at__date__lte=date_to
        ).order_by('-created_at')

    def _get_import_transactions(self, user, date_from, date_to):
        return []

    def _get_payment_transactions(self, user, date_from, date_to):
        from debit.models import DebitPayment

        return DebitPayment.objects.filter(
            user=user,
            created_at__date__gte=date_from,
            created_at__date__lte=date_to
        ).order_by('-created_at')

    def _get_payment_method(self, status):
        payment_methods = {
            'paid': 'qr',
            'pending': 'debt',
            'cash': 'cash',
        }
        return payment_methods.get(status, 'cash')

    def _calculate_stats(self, transactions, sales_query, imports_query, payment_query):
        total_sales = sum(1 for t in transactions if t['type'] == 'sale')
        total_imports = sum(1 for t in transactions if t['type'] == 'import')
        total_payments = sum(1 for t in transactions if t['type'] == 'payment')
        total_refunds = sum(1 for t in transactions if t['type'] == 'refund')

        period_revenue = sum(t['amount']
                             for t in transactions if t['type'] == 'sale')
        period_expenses = sum(t['amount']
                              for t in transactions if t['type'] == 'import')
        net_amount = period_revenue - period_expenses

        return {
            'total_sales': total_sales,
            'total_imports': total_imports,
            'total_payments': total_payments,
            'total_refunds': total_refunds,
            'total_transactions': len(transactions),
            'period_revenue': period_revenue,
            'period_expenses': period_expenses,
            'net_amount': net_amount,
        }
