from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from django.db.models import Sum, Count, F, ExpressionWrapper, DecimalField, Q
from django.utils.timezone import now
from datetime import timedelta, datetime
import calendar
import json
import traceback
from core.models import Product, Category
from core.models import Payment

class GetBusinessReport(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            period = request.query_params.get('period', 'month')
            date_from = request.query_params.get('date_from')
            date_to = request.query_params.get('date_to')

            if period == 'custom' and date_from and date_to:
                try:
                    start_date = datetime.strptime(date_from, '%Y-%m-%d').date()
                    end_date = datetime.strptime(date_to, '%Y-%m-%d').date()

                    if start_date > end_date:
                        return Response({
                            "status": "2",
                            "response": {
                                "error_code": "001",
                                "error_message_us": "Invalid date range",
                                "error_message_vn": "Ngày bắt đầu phải nhỏ hơn hoặc bằng ngày kết thúc"
                            }
                        }, status=status.HTTP_400_BAD_REQUEST)

                    days_diff = (end_date - start_date).days
                    if days_diff > 730:
                        return Response({
                            "status": "2",
                            "response": {
                                "error_code": "002",
                                "error_message_us": "Date range too large",
                                "error_message_vn": "Khoảng thời gian không được vượt quá 730 ngày (2 năm)"
                            }
                        }, status=status.HTTP_400_BAD_REQUEST)

                    today = now().date()
                    if end_date > today:
                        return Response({
                            "status": "2",
                            "response": {
                                "error_code": "003",
                                "error_message_us": "End date cannot be in the future",
                                "error_message_vn": "Ngày kết thúc không được là ngày trong tương lai"
                            }
                        }, status=status.HTTP_400_BAD_REQUEST)
                except ValueError:
                    return Response({
                        "status": "2",
                        "response": {
                            "error_code": "004",
                            "error_message_us": "Invalid date format",
                            "error_message_vn": "Định dạng ngày không hợp lệ. Vui lòng sử dụng định dạng YYYY-MM-DD"
                        }
                    }, status=status.HTTP_400_BAD_REQUEST)
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
            traceback.print_exc()
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
                    for item in payment.order.items.all():
                        cost_price = float(item.cost_price) if item.cost_price else 0
                        quantity = int(item.quantity)
                        total_cost += cost_price * quantity
                except Exception:
                    continue
        return int(total_cost)

    def get_top_products(self, payments):
        product_sales = {}

        for payment in payments:
            if payment.order:
                try:
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
                    continue

        sorted_products = sorted(
            product_sales.values(),
            key=lambda x: x['revenue'],
            reverse=True
        )[:10]

        return sorted_products

    def get_monthly_revenue(self, start_date, end_date, payments):
        monthly_data = {}

        year = start_date.year
        month = start_date.month
        end_year = end_date.year
        end_month = end_date.month

        while (year < end_year) or (year == end_year and month <= end_month):
            month_key = f'{year}-{month:02d}'
            monthly_data[month_key] = {
                'month': f'{month:02d}/{year}',
                'revenue': 0,
                'orders': 0
            }

            month += 1
            if month > 12:
                month = 1
                year += 1

        for payment in payments:
            month_key = payment.created_at.strftime('%Y-%m')
            if month_key in monthly_data:
                monthly_data[month_key]['revenue'] += int(payment.amount)
                monthly_data[month_key]['orders'] += 1

        sorted_months = sorted(monthly_data.items())
        return [data for _, data in sorted_months]

    def calculate_growth(self, previous, current):
        if previous == 0:
            return 100.0 if current > 0 else 0.0
        try:
            growth = ((current - previous) / previous) * 100
            return round(growth, 2) if abs(growth) != float('inf') else 0.0
        except (ZeroDivisionError, TypeError, ValueError):
            return 0.0

    def calculate_profit_margin(self, revenue, profit):
        if revenue == 0 or revenue is None:
            return 0.0
        try:
            margin = (profit / revenue) * 100
            return round(margin, 2) if abs(margin) != float('inf') else 0.0
        except (ZeroDivisionError, TypeError, ValueError):
            return 0.0
