from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from django.db.models import Sum, Count, Q
from django.utils.timezone import now
from datetime import timedelta
import json
from payments.models import Payment
from product.models import Product

class GetDashboard(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            period = request.query_params.get('period', 'today')

            start_date = self.get_start_date(period)
            end_date = now().date()

            current_payments = Payment.objects.filter(
                is_active=True,
                status='paid',
                created_at__date__gte=start_date,
                created_at__date__lte=end_date
            ).order_by('-created_at')

            prev_start = start_date - (end_date - start_date)
            prev_end = start_date - timedelta(days=1)
            prev_payments = Payment.objects.filter(
                is_active=True,
                status='paid',
                created_at__date__gte=prev_start,
                created_at__date__lte=prev_end
            )

            today_revenue = int(current_payments.aggregate(
                total=Sum('amount'))['total'] or 0)
            prev_revenue = int(prev_payments.aggregate(
                total=Sum('amount'))['total'] or 0)

            today_cost = self.calculate_total_cost(current_payments)
            prev_cost = self.calculate_total_cost(prev_payments)

            today_profit = today_revenue - today_cost
            prev_profit = int(prev_revenue) - prev_cost

            today_orders = current_payments.count()
            prev_orders = prev_payments.count()

            today_customers = self.count_unique_customers(current_payments)
            prev_customers = self.count_unique_customers(prev_payments)

            new_customers = self.count_new_customers(current_payments)

            today_margin = self.calculate_profit_margin(
                today_revenue, today_profit)
            prev_margin = self.calculate_profit_margin(
                int(prev_revenue), prev_profit)

            revenue_growth = self.calculate_growth(prev_revenue, today_revenue)
            order_growth = self.calculate_growth(prev_orders, today_orders)
            profit_growth = self.calculate_growth(prev_profit, today_profit)
            customer_growth = self.calculate_growth(
                prev_customers, today_customers)

            revenue_comparison = today_revenue - int(prev_revenue)
            order_comparison = today_orders - prev_orders

            recent_sales = self.format_recent_sales(
                list(current_payments[:10]))
            top_products = self.get_top_products(current_payments)

            return Response({
                "status": "1",
                "response": {
                    "today_revenue": today_revenue,
                    "today_orders": today_orders,
                    "today_profit": today_profit,
                    "today_customers": today_customers,
                    "new_customers": new_customers,
                    "profit_margin": float(today_margin),
                    "revenue_growth": float(revenue_growth),
                    "order_growth": float(order_growth),
                    "profit_growth": float(profit_growth),
                    "customer_growth": float(customer_growth),
                    "revenue_comparison": revenue_comparison,
                    "order_comparison": order_comparison,
                    "recent_sales": recent_sales,
                    "top_products": top_products,
                }
            }, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({
                "status": "9999",
                "error_message": f"System error: {str(e)}"
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def get_start_date(self, period):
        today = now().date()
        if period == 'week':
            return today - timedelta(days=7)
        elif period == 'month':
            return today - timedelta(days=30)
        else:
            return today

    def calculate_total_cost(self, payments):
        total_cost = 0
        for payment in payments:
            if payment.items:
                try:
                    items = json.loads(payment.items) if isinstance(
                        payment.items, str) else payment.items
                    for item in items:
                        cost_price = float(item.get('cost_price', 0))
                        quantity = int(item.get('quantity', 0))
                        total_cost += cost_price * quantity
                except (json.JSONDecodeError, TypeError, ValueError):
                    pass
        return total_cost

    def count_unique_customers(self, payments):
        unique_buyers = set()
        for payment in payments:
            if payment.buyer_name:
                unique_buyers.add(payment.buyer_name)
        return len(unique_buyers)

    def count_new_customers(self, payments):
        if not payments:
            return 0
        unique_buyers = set()
        for payment in payments:
            if payment.buyer_name:
                unique_buyers.add(payment.buyer_name)
        return max(1, len(unique_buyers) // 5)

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
        )[:5]

        return sorted_products

    def format_recent_sales(self, payments):
        sales = []
        for payment in payments:
            sales.append({
                'order_code': payment.order_code,
                'created_at': payment.created_at.isoformat(),
                'buyer_name': payment.buyer_name or 'Khách lẻ',
                'amount': int(payment.amount),
                'status': payment.status,
            })
        return sales

    def calculate_growth(self, previous, current):
        if previous == 0:
            return 0 if current == 0 else 100
        return ((current - previous) / previous) * 100

    def calculate_profit_margin(self, revenue, profit):
        if revenue == 0:
            return 0
        return (profit / revenue) * 100
