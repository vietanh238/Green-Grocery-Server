from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from django.db.models import Sum, Count, F, Q, Avg
from django.utils.timezone import now
from datetime import timedelta, datetime

from core.models import Product, InventoryTransaction, PurchaseOrder, Order


class InventoryMovementReport(APIView):
    """Báo cáo xuất nhập tồn kho"""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            start_date_str = request.GET.get('start_date')
            end_date_str = request.GET.get('end_date')

            if start_date_str and end_date_str:
                start_date = datetime.fromisoformat(start_date_str.replace('Z', '+00:00'))
                end_date = datetime.fromisoformat(end_date_str.replace('Z', '+00:00'))
            else:
                end_date = now()
                start_date = end_date - timedelta(days=30)

            # Get all transactions in period
            transactions = InventoryTransaction.objects.filter(
                created_at__gte=start_date,
                created_at__lte=end_date,
                created_by=request.user
            ).select_related('product', 'created_by')

            # Calculate summary
            total_import = transactions.filter(
                transaction_type='import'
            ).aggregate(total=Sum('quantity'))['total'] or 0

            total_export = abs(transactions.filter(
                transaction_type='export'
            ).aggregate(total=Sum('quantity'))['total'] or 0)

            total_damage = abs(transactions.filter(
                transaction_type='damage'
            ).aggregate(total=Sum('quantity'))['total'] or 0)

            total_lost = abs(transactions.filter(
                transaction_type='lost'
            ).aggregate(total=Sum('quantity'))['total'] or 0)

            total_import_value = transactions.filter(
                transaction_type='import'
            ).aggregate(total=Sum('total_value'))['total'] or 0

            total_export_value = transactions.filter(
                transaction_type='export'
            ).aggregate(total=Sum('total_value'))['total'] or 0

            # Get products with most movement
            product_movement = {}
            for txn in transactions:
                product_id = txn.product_id
                if product_id not in product_movement:
                    product_movement[product_id] = {
                        'product_name': txn.product.name if txn.product else 'N/A',
                        'sku': txn.product.sku if txn.product else 'N/A',
                        'import': 0,
                        'export': 0,
                        'damage': 0,
                        'lost': 0,
                        'net_change': 0
                    }

                qty = txn.quantity
                if txn.transaction_type == 'import':
                    product_movement[product_id]['import'] += qty
                elif txn.transaction_type == 'export':
                    product_movement[product_id]['export'] += abs(qty)
                elif txn.transaction_type == 'damage':
                    product_movement[product_id]['damage'] += abs(qty)
                elif txn.transaction_type == 'lost':
                    product_movement[product_id]['lost'] += abs(qty)

                product_movement[product_id]['net_change'] += qty

            # Sort by total movement
            top_movement = sorted(
                product_movement.values(),
                key=lambda x: abs(x['import']) + abs(x['export']) + abs(x['damage']) + abs(x['lost']),
                reverse=True
            )[:20]

            # Transaction breakdown by type
            transaction_breakdown = {
                'import': {
                    'count': transactions.filter(transaction_type='import').count(),
                    'quantity': total_import,
                    'value': float(total_import_value)
                },
                'export': {
                    'count': transactions.filter(transaction_type='export').count(),
                    'quantity': total_export,
                    'value': float(total_export_value)
                },
                'damage': {
                    'count': transactions.filter(transaction_type='damage').count(),
                    'quantity': total_damage,
                    'value': float(transactions.filter(transaction_type='damage').aggregate(total=Sum('total_value'))['total'] or 0)
                },
                'lost': {
                    'count': transactions.filter(transaction_type='lost').count(),
                    'quantity': total_lost,
                    'value': float(transactions.filter(transaction_type='lost').aggregate(total=Sum('total_value'))['total'] or 0)
                },
                'adjustment': {
                    'count': transactions.filter(transaction_type='adjustment').count(),
                }
            }

            return Response({
                'status': '1',
                'response': {
                    'summary': {
                        'total_import': total_import,
                        'total_export': total_export,
                        'total_damage': total_damage,
                        'total_lost': total_lost,
                        'net_change': total_import - total_export - total_damage - total_lost,
                        'total_import_value': float(total_import_value),
                        'total_export_value': float(total_export_value),
                        'transactions_count': transactions.count()
                    },
                    'transaction_breakdown': transaction_breakdown,
                    'top_movement_products': top_movement,
                    'period': {
                        'start': start_date.isoformat(),
                        'end': end_date.isoformat()
                    }
                }
            }, status=status.HTTP_200_OK)

        except Exception as ex:
            return Response({
                'status': '2',
                'response': {
                    'error_code': '9999',
                    'error_message_vn': f'Lỗi hệ thống: {str(ex)}'
                }
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class SupplierPerformanceReport(APIView):
    """Báo cáo hiệu suất nhà cung cấp"""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            start_date_str = request.GET.get('start_date')
            end_date_str = request.GET.get('end_date')

            if start_date_str and end_date_str:
                start_date = datetime.fromisoformat(start_date_str.replace('Z', '+00:00'))
                end_date = datetime.fromisoformat(end_date_str.replace('Z', '+00:00'))
            else:
                end_date = now()
                start_date = end_date - timedelta(days=90)

            # Get purchase orders in period
            purchase_orders = PurchaseOrder.objects.filter(
                created_at__gte=start_date,
                created_at__lte=end_date,
                created_by=request.user
            ).select_related('supplier')

            # Aggregate by supplier
            supplier_stats = {}
            for po in purchase_orders:
                if not po.supplier:
                    continue

                supplier_id = po.supplier.id
                if supplier_id not in supplier_stats:
                    supplier_stats[supplier_id] = {
                        'supplier_name': po.supplier.name,
                        'supplier_code': po.supplier.supplier_code,
                        'total_orders': 0,
                        'total_amount': 0,
                        'completed_orders': 0,
                        'pending_orders': 0,
                        'cancelled_orders': 0,
                        'avg_delivery_days': 0,
                        'on_time_delivery': 0,
                        'late_delivery': 0
                    }

                supplier_stats[supplier_id]['total_orders'] += 1
                supplier_stats[supplier_id]['total_amount'] += float(po.total_amount)

                if po.status == 'completed':
                    supplier_stats[supplier_id]['completed_orders'] += 1
                elif po.status == 'pending':
                    supplier_stats[supplier_id]['pending_orders'] += 1
                elif po.status == 'cancelled':
                    supplier_stats[supplier_id]['cancelled_orders'] += 1

                # Calculate delivery performance
                if po.received_date and po.expected_date:
                    delivery_days = (po.received_date.date() - po.created_at.date()).days
                    expected_days = (po.expected_date.date() - po.created_at.date()).days

                    if delivery_days <= expected_days:
                        supplier_stats[supplier_id]['on_time_delivery'] += 1
                    else:
                        supplier_stats[supplier_id]['late_delivery'] += 1

            # Calculate performance scores
            for stats in supplier_stats.values():
                total = stats['total_orders']
                if total > 0:
                    stats['completion_rate'] = round((stats['completed_orders'] / total) * 100, 2)
                    stats['on_time_rate'] = round((stats['on_time_delivery'] / total) * 100, 2) if (stats['on_time_delivery'] + stats['late_delivery']) > 0 else 0
                    stats['total_amount'] = int(stats['total_amount'])
                else:
                    stats['completion_rate'] = 0
                    stats['on_time_rate'] = 0

            # Sort by total amount
            top_suppliers = sorted(
                supplier_stats.values(),
                key=lambda x: x['total_amount'],
                reverse=True
            )

            # Summary
            total_pos = purchase_orders.count()
            total_po_value = sum(float(po.total_amount) for po in purchase_orders)

            return Response({
                'status': '1',
                'response': {
                    'summary': {
                        'total_purchase_orders': total_pos,
                        'total_value': int(total_po_value),
                        'unique_suppliers': len(supplier_stats)
                    },
                    'suppliers': top_suppliers,
                    'period': {
                        'start': start_date.isoformat(),
                        'end': end_date.isoformat()
                    }
                }
            }, status=status.HTTP_200_OK)

        except Exception as ex:
            return Response({
                'status': '2',
                'response': {
                    'error_code': '9999',
                    'error_message_vn': f'Lỗi hệ thống: {str(ex)}'
                }
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class CustomerBehaviorReport(APIView):
    """Báo cáo hành vi khách hàng"""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            start_date_str = request.GET.get('start_date')
            end_date_str = request.GET.get('end_date')

            if start_date_str and end_date_str:
                start_date = datetime.fromisoformat(start_date_str.replace('Z', '+00:00'))
                end_date = datetime.fromisoformat(end_date_str.replace('Z', '+00:00'))
            else:
                end_date = now()
                start_date = end_date - timedelta(days=30)

            # Get orders in period
            orders = Order.objects.filter(
                created_at__gte=start_date,
                created_at__lte=end_date,
                created_by=request.user,
                status='paid'
            ).prefetch_related('items__product')

            # Analyze customer behavior
            customer_data = {}
            walk_in_count = 0
            walk_in_total = 0

            for order in orders:
                if order.buyer_phone:
                    phone = order.buyer_phone
                    if phone not in customer_data:
                        customer_data[phone] = {
                            'name': order.buyer_name or 'N/A',
                            'phone': phone,
                            'visit_count': 0,
                            'total_spent': 0,
                            'avg_order_value': 0,
                            'last_visit': None
                        }

                    customer_data[phone]['visit_count'] += 1
                    customer_data[phone]['total_spent'] += float(order.total_amount)
                    customer_data[phone]['last_visit'] = order.created_at.isoformat()
                else:
                    walk_in_count += 1
                    walk_in_total += float(order.total_amount)

            # Calculate averages
            for customer in customer_data.values():
                customer['avg_order_value'] = int(customer['total_spent'] / customer['visit_count'])
                customer['total_spent'] = int(customer['total_spent'])

            # Segment customers
            vip_customers = [c for c in customer_data.values() if c['total_spent'] >= 1000000]  # >= 1M
            regular_customers = [c for c in customer_data.values() if 500000 <= c['total_spent'] < 1000000]  # 500K-1M
            occasional_customers = [c for c in customer_data.values() if c['total_spent'] < 500000]  # < 500K

            # Top customers
            top_customers = sorted(
                customer_data.values(),
                key=lambda x: x['total_spent'],
                reverse=True
            )[:20]

            # Payment method preferences
            cash_orders = orders.filter(payment_method='cash').count()
            qr_orders = orders.filter(payment_method='qr').count()

            return Response({
                'status': '1',
                'response': {
                    'summary': {
                        'total_customers': len(customer_data),
                        'walk_in_customers': walk_in_count,
                        'total_orders': orders.count(),
                        'avg_order_value': int(sum(float(o.total_amount) for o in orders) / orders.count()) if orders.count() > 0 else 0
                    },
                    'customer_segments': {
                        'vip': {
                            'count': len(vip_customers),
                            'total_revenue': sum(c['total_spent'] for c in vip_customers)
                        },
                        'regular': {
                            'count': len(regular_customers),
                            'total_revenue': sum(c['total_spent'] for c in regular_customers)
                        },
                        'occasional': {
                            'count': len(occasional_customers),
                            'total_revenue': sum(c['total_spent'] for c in occasional_customers)
                        },
                        'walk_in': {
                            'count': walk_in_count,
                            'total_revenue': walk_in_total
                        }
                    },
                    'top_customers': top_customers,
                    'payment_preferences': {
                        'cash': {
                            'count': cash_orders,
                            'percentage': round((cash_orders / orders.count() * 100), 2) if orders.count() > 0 else 0
                        },
                        'qr': {
                            'count': qr_orders,
                            'percentage': round((qr_orders / orders.count() * 100), 2) if orders.count() > 0 else 0
                        }
                    },
                    'period': {
                        'start': start_date.isoformat(),
                        'end': end_date.isoformat()
                    }
                }
            }, status=status.HTTP_200_OK)

        except Exception as ex:
            return Response({
                'status': '2',
                'response': {
                    'error_code': '9999',
                    'error_message_vn': f'Lỗi hệ thống: {str(ex)}'
                }
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

