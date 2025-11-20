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

            current_payments = Payment.objects.select_related('order').prefetch_related(
                'order__items__product'
            ).filter(
                is_active=True,
                status='paid',
                created_at__gte=start_date,
                created_at__lte=end_date
            )

            previous_payments = Payment.objects.select_related('order').prefetch_related(
                'order__items__product'
            ).filter(
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

            today_customers = current_payments.filter(
                order__buyer_phone__isnull=False
            ).values('order__buyer_phone').distinct().count()
            new_customers = current_payments.filter(
                order__buyer_phone__isnull=False
            ).values('order__buyer_phone').distinct().count()

            revenue_growth = self.calculate_growth(prev_revenue, today_revenue)
            order_growth = self.calculate_growth(prev_orders, today_orders)
            profit_growth = self.calculate_growth(prev_profit, today_profit)
            customer_growth = 0

            profit_margin = self.calculate_profit_margin(
                today_revenue, today_profit)

            recent_sales = self.get_recent_sales(current_payments)
            top_products = self.get_top_products(current_payments)
            hourly_revenue = self.get_hourly_revenue(current_payments, period)

            # Get inventory alerts
            inventory_stats = self.get_inventory_stats()
            low_stock_products = self.get_low_stock_products()

            # ✅ Enhanced metrics for WinMart/CircleK standard
            avg_order_value = float(today_revenue / today_orders) if today_orders > 0 else 0
            payment_methods_breakdown = self.get_payment_methods_breakdown(current_payments)
            category_revenue = self.get_category_revenue(current_payments)
            inventory_valuation = self.get_inventory_valuation()
            peak_hour = self.get_peak_hour(current_payments)

            return Response({
                "status": "1",
                "response": {
                    # Core metrics
                    "today_revenue": int(today_revenue),
                    "today_orders": today_orders,
                    "today_profit": today_profit,
                    "today_customers": today_customers,
                    "new_customers": new_customers,
                    "profit_margin": float(profit_margin),
                    "avg_order_value": float(avg_order_value),

                    # Growth metrics
                    "revenue_growth": float(revenue_growth),
                    "order_growth": float(order_growth),
                    "profit_growth": float(profit_growth),
                    "customer_growth": float(customer_growth),
                    "revenue_comparison": int(today_revenue) - int(prev_revenue),
                    "order_comparison": today_orders - prev_orders,

                    # Sales data
                    "recent_sales": recent_sales,
                    "top_products": top_products,
                    "hourly_revenue": hourly_revenue,
                    "peak_hour": peak_hour,

                    # Inventory
                    "inventory_stats": inventory_stats,
                    "inventory_valuation": inventory_valuation,
                    "low_stock_products": low_stock_products,

                    # Analytics
                    "payment_methods": payment_methods_breakdown,
                    "category_revenue": category_revenue,
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
            if payment.order:
                try:
                    # Access items through order relationship
                    for item in payment.order.items.all():
                        profit = float(item.profit) if item.profit else 0
                        total_profit += profit
                except Exception:
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
                'buyer_name': payment.order.buyer_name if payment.order and payment.order.buyer_name else 'Khách lẻ',
                'amount': int(payment.amount),
                'status': payment.status
            }
            for payment in sales
        ]

    def get_top_products(self, payments):
        product_sales = {}

        for payment in payments:
            if payment.order:
                try:
                    # Access items through order relationship
                    for item in payment.order.items.all():
                        sku = item.product_sku
                        name = item.product_name
                        quantity = item.quantity
                        price = float(item.unit_price)

                        if sku not in product_sales:
                            product_sales[sku] = {
                                'name': name,
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

    def get_inventory_stats(self):
        """Get inventory statistics"""
        try:
            all_products = Product.objects.filter(is_active=True)

            total_products = all_products.count()

            low_stock = all_products.filter(
                stock_quantity__gt=0,
                stock_quantity__lte=F('reorder_point')
            ).count()

            out_of_stock = all_products.filter(stock_quantity=0).count()

            overstock = all_products.filter(
                stock_quantity__gt=F('max_stock_level')
            ).count()

            total_stock_value = all_products.aggregate(
                total=Sum(F('stock_quantity') * F('cost_price'))
            )['total'] or 0

            return {
                'total_products': total_products,
                'low_stock_count': low_stock,
                'out_of_stock_count': out_of_stock,
                'overstock_count': overstock,
                'total_stock_value': float(total_stock_value),
                'alert_level': 'critical' if out_of_stock > 0 else 'warning' if low_stock > 0 else 'normal'
            }
        except Exception as e:
            return {
                'total_products': 0,
                'low_stock_count': 0,
                'out_of_stock_count': 0,
                'overstock_count': 0,
                'total_stock_value': 0,
                'alert_level': 'normal'
            }

    def get_low_stock_products(self):
        """Get list of products with low stock or out of stock"""
        try:
            # Get products that are out of stock or low stock
            products = Product.objects.filter(
                Q(stock_quantity=0) |
                Q(stock_quantity__gt=0, stock_quantity__lte=F('reorder_point')),
                is_active=True
            ).select_related('category').order_by('stock_quantity')[:10]

            result = []
            for product in products:
                result.append({
                    'id': product.id,
                    'name': product.name,
                    'sku': product.sku,
                    'stock_quantity': product.stock_quantity,
                    'reorder_point': product.reorder_point,
                    'unit': product.unit,
                    'category': product.category.name if product.category else 'N/A',
                    'status': 'out_of_stock' if product.stock_quantity == 0 else 'low_stock',
                    'urgency': 'critical' if product.stock_quantity == 0 else 'high' if product.stock_quantity <= product.reorder_point // 2 else 'medium'
                })

            return result
        except Exception as e:
            return []

    def get_payment_methods_breakdown(self, payments):
        """Get revenue breakdown by payment methods"""
        try:
            cash_count = 0
            qr_count = 0
            cash_total = 0
            qr_total = 0

            for payment in payments:
                if payment.order:
                    if payment.order.payment_method == 'cash':
                        cash_count += 1
                        cash_total += float(payment.amount)
                    elif payment.order.payment_method == 'qr':
                        qr_count += 1
                        qr_total += float(payment.amount)

            total_revenue = cash_total + qr_total

            return {
                'cash': {
                    'count': cash_count,
                    'total': int(cash_total),
                    'percentage': round((cash_total / total_revenue * 100), 2) if total_revenue > 0 else 0
                },
                'qr': {
                    'count': qr_count,
                    'total': int(qr_total),
                    'percentage': round((qr_total / total_revenue * 100), 2) if total_revenue > 0 else 0
                }
            }
        except Exception as e:
            return {'cash': {'count': 0, 'total': 0, 'percentage': 0}, 'qr': {'count': 0, 'total': 0, 'percentage': 0}}

    def get_category_revenue(self, payments):
        """Get revenue breakdown by product categories"""
        try:
            category_data = {}

            for payment in payments:
                if payment.order:
                    for item in payment.order.items.all():
                        if item.product and item.product.category:
                            category_name = item.product.category.name
                            revenue = float(item.total_price)

                            if category_name not in category_data:
                                category_data[category_name] = {
                                    'revenue': 0,
                                    'quantity': 0,
                                    'items_count': 0
                                }

                            category_data[category_name]['revenue'] += revenue
                            category_data[category_name]['quantity'] += item.quantity
                            category_data[category_name]['items_count'] += 1

            # Sort by revenue and get top 10
            sorted_categories = sorted(
                [{'name': name, **data} for name, data in category_data.items()],
                key=lambda x: x['revenue'],
                reverse=True
            )[:10]

            # Calculate percentages
            total_revenue = sum(cat['revenue'] for cat in sorted_categories)
            for cat in sorted_categories:
                cat['revenue'] = int(cat['revenue'])
                cat['percentage'] = round((cat['revenue'] / total_revenue * 100), 2) if total_revenue > 0 else 0

            return sorted_categories
        except Exception as e:
            return []

    def get_inventory_valuation(self):
        """Get detailed inventory valuation"""
        try:
            all_products = Product.objects.filter(is_active=True)

            total_value = sum(
                float(p.stock_quantity * p.cost_price) for p in all_products
            )

            total_retail_value = sum(
                float(p.stock_quantity * p.price) for p in all_products
            )

            potential_profit = total_retail_value - total_value

            return {
                'total_cost_value': int(total_value),
                'total_retail_value': int(total_retail_value),
                'potential_profit': int(potential_profit),
                'profit_margin': round((potential_profit / total_retail_value * 100), 2) if total_retail_value > 0 else 0
            }
        except Exception as e:
            return {
                'total_cost_value': 0,
                'total_retail_value': 0,
                'potential_profit': 0,
                'profit_margin': 0
            }

    def get_peak_hour(self, payments):
        """Get the peak sales hour"""
        try:
            hourly_revenue = {}
            hourly_orders = {}

            for payment in payments:
                hour = payment.created_at.hour
                amount = float(payment.amount)

                if hour not in hourly_revenue:
                    hourly_revenue[hour] = 0
                    hourly_orders[hour] = 0

                hourly_revenue[hour] += amount
                hourly_orders[hour] += 1

            if not hourly_revenue:
                return None

            peak_hour = max(hourly_revenue, key=hourly_revenue.get)

            return {
                'hour': peak_hour,
                'revenue': int(hourly_revenue[peak_hour]),
                'orders': hourly_orders[peak_hour],
                'label': f"{peak_hour}:00 - {peak_hour + 1}:00"
            }
        except Exception as e:
            return None
