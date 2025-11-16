from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from django.db.models import Sum, Count, F, Q
from django.utils.timezone import now
from datetime import timedelta, datetime
import json
from core.models import Payment
from core.models import Product, Category


class GetDashboardView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            period = request.query_params.get('period', 'today')

            start_date, end_date = self.get_date_range(period)
            prev_start, prev_end = self.get_previous_date_range(
                period, start_date)

            current_payments = Payment.objects.filter(
                is_active=True,
                status='paid',
                created_at__gte=start_date,
                created_at__lte=end_date
            )

            previous_payments = Payment.objects.filter(
                is_active=True,
                status='paid',
                created_at__gte=prev_start,
                created_at__lte=prev_end
            )

            today_revenue = current_payments.aggregate(
                total=Sum('amount'))['total'] or 0
            today_orders = current_payments.count()
            today_profit = self.calculate_total_profit(current_payments)

            prev_revenue = previous_payments.aggregate(
                total=Sum('amount'))['total'] or 0
            prev_orders = previous_payments.count()
            prev_profit = self.calculate_total_profit(previous_payments)

            today_customers = current_payments.values(
                'buyer_phone').distinct().count()
            new_customers = current_payments.filter(
                buyer_phone__isnull=False
            ).values('buyer_phone').distinct().count()

            revenue_growth = self.calculate_growth(prev_revenue, today_revenue)
            order_growth = self.calculate_growth(prev_orders, today_orders)
            profit_growth = self.calculate_growth(prev_profit, today_profit)
            customer_growth = 0

            profit_margin = self.calculate_profit_margin(
                today_revenue, today_profit)

            recent_sales = self.get_recent_sales(current_payments)
            top_products = self.get_top_products(current_payments)
            hourly_revenue = self.get_hourly_revenue(current_payments, period)

            return Response({
                "status": "1",
                "response": {
                    "today_revenue": int(today_revenue),
                    "today_orders": today_orders,
                    "today_profit": today_profit,
                    "today_customers": today_customers,
                    "new_customers": new_customers,
                    "profit_margin": float(profit_margin),
                    "revenue_growth": float(revenue_growth),
                    "order_growth": float(order_growth),
                    "profit_growth": float(profit_growth),
                    "customer_growth": float(customer_growth),
                    "revenue_comparison": int(today_revenue) - int(prev_revenue),
                    "order_comparison": today_orders - prev_orders,
                    "recent_sales": recent_sales,
                    "top_products": top_products,
                    "hourly_revenue": hourly_revenue,
                }
            }, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({
                "status": "9999",
                "error_message": f"System error: {str(e)}"
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def get_date_range(self, period):
        today = now()

        if period == 'today':
            start_date = today.replace(
                hour=0, minute=0, second=0, microsecond=0)
            end_date = today
        elif period == 'week':
            start_date = today - timedelta(days=today.weekday())
            start_date = start_date.replace(
                hour=0, minute=0, second=0, microsecond=0)
            end_date = today
        elif period == 'month':
            start_date = today.replace(
                day=1, hour=0, minute=0, second=0, microsecond=0)
            end_date = today
        else:
            start_date = today.replace(
                hour=0, minute=0, second=0, microsecond=0)
            end_date = today

        return start_date, end_date

    def get_previous_date_range(self, period, current_start):
        if period == 'today':
            prev_start = current_start - timedelta(days=1)
            prev_end = current_start - timedelta(seconds=1)
        elif period == 'week':
            prev_start = current_start - timedelta(days=7)
            prev_end = current_start - timedelta(seconds=1)
        elif period == 'month':
            if current_start.month == 1:
                prev_start = current_start.replace(
                    year=current_start.year - 1, month=12, day=1)
            else:
                prev_start = current_start.replace(
                    month=current_start.month - 1, day=1)
            prev_end = current_start - timedelta(seconds=1)
        else:
            prev_start = current_start - timedelta(days=1)
            prev_end = current_start - timedelta(seconds=1)

        return prev_start, prev_end

    def calculate_total_profit(self, payments):
        total_profit = 0
        for payment in payments:
            if payment.items:
                try:
                    items = json.loads(payment.items) if isinstance(
                        payment.items, str) else payment.items
                    for item in items:
                        cost_price = float(item.get('cost_price', 0))
                        price = float(item.get('price', 0))
                        quantity = int(item.get('quantity', 0))
                        profit = (price - cost_price) * quantity
                        total_profit += profit
                except (json.JSONDecodeError, TypeError, ValueError):
                    pass
        return int(total_profit)

    def calculate_growth(self, previous, current):
        if previous == 0:
            return 100 if current > 0 else 0
        return ((current - previous) / previous) * 100

    def calculate_profit_margin(self, revenue, profit):
        if revenue == 0:
            return 0
        return (profit / revenue) * 100

    def get_recent_sales(self, payments):
        sales = payments.order_by('-created_at')[:10]
        return [
            {
                'order_code': payment.order_code,
                'created_at': payment.created_at.isoformat(),
                'buyer_name': payment.buyer_name or 'Khách lẻ',
                'amount': int(payment.amount),
                'status': payment.status
            }
            for payment in sales
        ]

    def get_top_products(self, payments):
        product_sales = {}

        for payment in payments:
            if payment.items:
                try:
                    items = json.loads(payment.items) if isinstance(
                        payment.items, str) else payment.items
                    for item in items:
                        sku = item.get('sku', 'unknown')
                        name = item.get('name', '')
                        quantity = int(item.get('quantity', 0))
                        price = float(item.get('price', 0))

                        if sku not in product_sales:
                            product_sales[sku] = {
                                'name': name,
                                'quantity': 0,
                                'revenue': 0
                            }

                        product_sales[sku]['quantity'] += quantity
                        product_sales[sku]['revenue'] += int(quantity * price)
                except (json.JSONDecodeError, TypeError, ValueError):
                    pass

        sorted_products = sorted(
            product_sales.values(),
            key=lambda x: x['revenue'],
            reverse=True
        )[:10]

        return sorted_products

    def get_hourly_revenue(self, payments, period):
        revenue_data = []

        if period == 'today':
            hourly_revenue = {}
            for hour in range(24):
                hourly_revenue[hour] = 0

            for payment in payments:
                hour = payment.created_at.hour
                hourly_revenue[hour] += int(payment.amount)

            revenue_data = [
                {
                    'hour': hour,
                    'revenue': amount
                }
                for hour, amount in sorted(hourly_revenue.items())
            ]

        elif period == 'week':
            daily_revenue = {}
            start_date = now() - timedelta(days=now().weekday())

            for i in range(7):
                date = (start_date + timedelta(days=i)).date()
                daily_revenue[date] = 0

            for payment in payments:
                date = payment.created_at.date()
                if date in daily_revenue:
                    daily_revenue[date] += int(payment.amount)

            revenue_data = [
                {
                    'date': date.isoformat(),
                    'revenue': amount
                }
                for date, amount in sorted(daily_revenue.items())
            ]

        elif period == 'month':
            daily_revenue = {}
            start_date = now().replace(day=1)
            current_date = start_date

            while current_date.month == start_date.month:
                daily_revenue[current_date.date()] = 0
                current_date += timedelta(days=1)

            for payment in payments:
                date = payment.created_at.date()
                if date in daily_revenue:
                    daily_revenue[date] += int(payment.amount)

            revenue_data = [
                {
                    'date': date.isoformat(),
                    'revenue': amount
                }
                for date, amount in sorted(daily_revenue.items())
            ]

        return revenue_data
