from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from django.db.models import Sum, Count, F, ExpressionWrapper, DecimalField, Q
from django.utils.timezone import now
from datetime import timedelta
import json
from core.models import Product, Category
from core.models import Payment
from datetime import timedelta, datetime

class GetBusinessReport(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            period = request.query_params.get('period', 'month')
            date_from = request.query_params.get('date_from')
            date_to = request.query_params.get('date_to')

            if period == 'custom' and date_from and date_to:
                start_date = datetime.strptime(date_from, '%Y-%m-%d').date()
                end_date = datetime.strptime(date_to, '%Y-%m-%d').date()
            else:
                start_date = self.get_start_date(period)
                end_date = now().date()

            current_payments = Payment.objects.select_related('order').prefetch_related(
                'order__items__product'
            ).filter(
                is_active=True,
                status='paid',
                created_at__date__gte=start_date,
                created_at__date__lte=end_date
            )

            prev_start = start_date - (end_date - start_date)
            prev_end = start_date - timedelta(days=1)
            prev_payments = Payment.objects.select_related('order').prefetch_related(
                'order__items__product'
            ).filter(
                is_active=True,
                status='paid',
                created_at__date__gte=prev_start,
                created_at__date__lte=prev_end
            )

            current_revenue = current_payments.aggregate(
                total=Sum('amount'))['total'] or 0
            prev_revenue = prev_payments.aggregate(
                total=Sum('amount'))['total'] or 0

            current_cost = self.calculate_total_cost(current_payments)
            prev_cost = self.calculate_total_cost(prev_payments)

            current_profit = int(current_revenue) - current_cost
            prev_profit = int(prev_revenue) - prev_cost

            current_orders = current_payments.count()
            prev_orders = prev_payments.count()

            current_margin = self.calculate_profit_margin(
                int(current_revenue), current_profit)
            prev_margin = self.calculate_profit_margin(
                int(prev_revenue), prev_profit)

            revenue_growth = self.calculate_growth(
                int(prev_revenue), int(current_revenue))
            profit_growth = self.calculate_growth(prev_profit, current_profit)
            order_growth = self.calculate_growth(prev_orders, current_orders)
            margin_growth = current_margin - prev_margin

            top_products = self.get_top_products(current_payments)
            monthly_revenue = self.get_monthly_revenue(
                start_date, end_date, current_payments)

            return Response({
                "status": "1",
                "response": {
                    "total_revenue": int(current_revenue),
                    "total_profit": current_profit,
                    "profit_margin": float(current_margin),
                    "orders_count": current_orders,
                    "revenue_growth": float(revenue_growth),
                    "profit_growth": float(profit_growth),
                    "order_growth": float(order_growth),
                    "margin_growth": float(margin_growth),
                    "revenue_comparison": int(current_revenue) - int(prev_revenue),
                    "profit_comparison": current_profit - prev_profit,
                    "order_comparison": current_orders - prev_orders,
                    "top_products": top_products,
                    "monthly_revenue": monthly_revenue,
                }
            }, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({
                "status": "2",
                "response": {
                    "error_code": "9999",
                    "error_message_us": "System error",
                    "error_message_vn": f"Lỗi hệ thống: {str(e)}"
                }
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def get_start_date(self, period):
        today = now().date()
        if period == 'week':
            return today - timedelta(days=7)
        elif period == 'year':
            return today - timedelta(days=365)
        else:
            return today - timedelta(days=30)

    def calculate_total_cost(self, payments):
        total_cost = 0
        for payment in payments:
            if payment.order:
                try:
                    # Access items through order relationship
                    for item in payment.order.items.all():
                        cost_price = float(item.cost_price)
                        quantity = int(item.quantity)
                        total_cost += cost_price * quantity
                except Exception:
                    pass
        return total_cost

    def get_top_products(self, payments):
        product_sales = {}

        for payment in payments:
            if payment.order:
                try:
                    # Access items through order relationship
                    for item in payment.order.items.all():
                        sku = item.product_sku
                        name = item.product_name
                        quantity = int(item.quantity)
                        price = float(item.unit_price)

                        if sku not in product_sales:
                            product_sales[sku] = {
                                'name': name,
                                'sku': sku,
                                'quantity': 0,
                                'revenue': 0
                            }

                        product_sales[sku]['quantity'] += quantity
                        product_sales[sku]['revenue'] += int(quantity * price)
                except Exception:
                    pass

        sorted_products = sorted(
            product_sales.values(),
            key=lambda x: x['revenue'],
            reverse=True
        )[:5]

        return sorted_products

    def get_monthly_revenue(self, start_date, end_date, payments):
        monthly_data = {}

        current = start_date
        while current <= end_date:
            month_key = current.strftime('%Y-%m')
            if month_key not in monthly_data:
                monthly_data[month_key] = {
                    'month': month_key,
                    'revenue': 0,
                    'orders': 0
                }
            current += timedelta(days=1)

        for payment in payments:
            month_key = payment.created_at.strftime('%Y-%m')
            if month_key in monthly_data:
                monthly_data[month_key]['revenue'] += int(payment.amount)
                monthly_data[month_key]['orders'] += 1

        sorted_months = sorted(monthly_data.items())
        return [data for _, data in sorted_months]

    def calculate_growth(self, previous, current):
        if previous == 0:
            return 0 if current == 0 else 100
        return ((current - previous) / previous) * 100

    def calculate_profit_margin(self, revenue, profit):
        if revenue == 0:
            return 0
        return (profit / revenue) * 100
