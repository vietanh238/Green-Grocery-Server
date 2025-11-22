from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from django.db.models import Sum, F
from datetime import datetime, timedelta
from .ai_service import ai_forecast_service
from core.models import Product, Category
from core.models import Order, OrderItem


class TrainAIModelView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        try:
            cutoff_date = datetime.now() - timedelta(days=90)

            orders = Order.objects.filter(
                created_by=request.user,
                created_at__gte=cutoff_date,
                status='paid'
            ).select_related('created_by')

            if not orders.exists():
                return Response({
                    'status': '2',
                    'response': {
                        'error_code': '001',
                        'error_message_vn': 'Không có đơn hàng nào trong 90 ngày qua.',
                        'suggestion': 'Hãy bán hàng và tạo đơn hàng trước khi train AI. Cần ít nhất 5 giao dịch bán hàng.'
                    }
                }, status=status.HTTP_400_BAD_REQUEST)

            sales_history = []
            skipped_items = 0

            for order in orders:
                order_items = OrderItem.objects.filter(
                    order=order
                ).select_related('product')

                for item in order_items:
                    # Check if product exists and has valid data
                    if not item.product:
                        skipped_items += 1
                        continue

                    if not item.product.id:
                        skipped_items += 1
                        continue

                    try:
                        sales_history.append({
                            'product_id': item.product.id,
                            'quantity': item.quantity,
                            'total_amount': float(item.quantity * item.unit_price),
                            'created_at': order.created_at.isoformat()
                        })
                    except (ValueError, TypeError) as e:
                        print(f"Error processing order item {item.id}: {str(e)}")
                        skipped_items += 1
                        continue

            if len(sales_history) < 5:
                return Response({
                    'status': '2',
                    'response': {
                        'error_code': '001',
                        'error_message_vn': f'Cần ít nhất 5 giao dịch để train AI. Hiện tại có {len(sales_history)} giao dịch hợp lệ.',
                        'suggestion': 'Hãy tích lũy thêm dữ liệu bán hàng. Lý tưởng nhất là có dữ liệu từ nhiều ngày khác nhau để AI học được pattern theo thời gian.',
                        'debug_info': f'Đã bỏ qua {skipped_items} mục do thiếu thông tin sản phẩm.' if skipped_items > 0 else None
                    }
                }, status=status.HTTP_400_BAD_REQUEST)

            success = ai_forecast_service.train(sales_history)

            if success:
                return Response({
                    'status': '1',
                    'response': {
                        'message': 'Đã train AI thành công!',
                        'total_transactions': len(sales_history),
                        'trained_at': datetime.now().isoformat(),
                        'products_analyzed': len(set(s['product_id'] for s in sales_history)),
                        'skipped_items': skipped_items
                    }
                }, status=status.HTTP_200_OK)
            else:
                return Response({
                    'status': '2',
                    'response': {
                        'error_code': '002',
                        'error_message_vn': 'Không đủ dữ liệu để train AI',
                        'suggestion': 'Dữ liệu bán hàng chưa đủ đa dạng hoặc chưa đủ nhiều. Hãy tiếp tục bán hàng thêm.'
                    }
                }, status=status.HTTP_400_BAD_REQUEST)

        except Exception as ex:
            import traceback
            error_trace = traceback.format_exc()
            print(f"Train AI error: {error_trace}")

            return Response({
                'status': '2',
                'response': {
                    'error_code': '9999',
                    'error_message_vn': f'Lỗi hệ thống: {str(ex)}',
                    'error_details': error_trace if request.user.is_staff else None
                }
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class GetReorderRecommendationsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            products = Product.objects.filter(
                created_by=request.user,
                is_active=True
            ).select_related('category')

            if not products.exists():
                return Response({
                    'status': '1',
                    'response': {
                        'recommendations': [],
                        'summary': {
                            'total_products_need_reorder': 0,
                            'high_urgency': 0,
                            'medium_urgency': 0,
                            'low_urgency': 0,
                            'critical_urgency': 0,
                            'total_estimated_cost': 0
                        },
                        'message': 'Không có sản phẩm nào trong hệ thống'
                    }
                }, status=status.HTTP_200_OK)

            cutoff_date = datetime.now() - timedelta(days=60)
            orders = Order.objects.filter(
                created_by=request.user,
                created_at__gte=cutoff_date,
                status='paid'
            ).select_related('created_by')

            all_sales = []
            for order in orders:
                items = OrderItem.objects.filter(
                    order=order
                ).select_related('product')

                for item in items:
                    if item.product:
                        all_sales.append({
                            'product_id': item.product.id,
                            'quantity': item.quantity,
                            'total_amount': float(item.quantity * item.unit_price),
                            'created_at': order.created_at.isoformat()
                        })

            recommendations = []

            for product in products:
                try:
                    product_sales = [s for s in all_sales if s['product_id'] == product.id]

                    # Skip if no sales history
                    if len(product_sales) < 1:
                        continue

                    predictions = ai_forecast_service.predict_demand(
                        product_id=product.id,
                        current_stock=product.stock_quantity,
                        sales_history=all_sales,
                        days_ahead=30
                    )

                    if not predictions:
                        continue

                    recommendation = ai_forecast_service.calculate_reorder_recommendation(
                        product_id=product.id,
                        current_stock=product.stock_quantity,
                        predictions=predictions,
                        lead_time_days=7
                    )

                    if recommendation and recommendation['should_reorder']:
                        recommendation['product_name'] = product.name
                        recommendation['product_sku'] = product.sku
                        recommendation['product_image'] = product.image if hasattr(product, 'image') else ''
                        recommendation['unit'] = product.unit
                        recommendation['cost_price'] = float(product.cost_price) if product.cost_price else 0
                        recommendation['estimated_cost'] = round(
                            recommendation['optimal_order_quantity'] * float(product.cost_price if product.cost_price else 0),
                            2
                        )
                        recommendations.append(recommendation)

                except Exception as product_error:
                    print(f"Error processing product {product.id}: {str(product_error)}")
                    continue

            # Sort by urgency
            urgency_order = {'critical': 0, 'high': 1, 'medium': 2, 'low': 3}
            recommendations.sort(key=lambda x: (
                urgency_order.get(x.get('urgency', 'low'), 3),
                x.get('days_until_stockout', 999)
            ))

            total_estimated_cost = sum(r.get('estimated_cost', 0) for r in recommendations)

            return Response({
                'status': '1',
                'response': {
                    'recommendations': recommendations,
                    'summary': {
                        'total_products_need_reorder': len(recommendations),
                        'critical_urgency': len([r for r in recommendations if r.get('urgency') == 'critical']),
                        'high_urgency': len([r for r in recommendations if r.get('urgency') == 'high']),
                        'medium_urgency': len([r for r in recommendations if r.get('urgency') == 'medium']),
                        'low_urgency': len([r for r in recommendations if r.get('urgency') == 'low']),
                        'total_estimated_cost': total_estimated_cost
                    }
                }
            }, status=status.HTTP_200_OK)

        except Exception as ex:
            import traceback
            error_trace = traceback.format_exc()
            print(f"Reorder recommendations error: {error_trace}")

            return Response({
                'status': '2',
                'response': {
                    'error_code': '9999',
                    'error_message_vn': f'Lỗi hệ thống: {str(ex)}',
                    'error_details': error_trace if request.user.is_staff else None
                }
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class GetProductForecastView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, product_id):
        try:

            try:
                product = Product.objects.get(id=product_id, created_by=request.user, is_active=True)
            except Product.DoesNotExist:
                return Response({
                    'status': '2',
                    'response': {
                        'error_message_vn': 'Không tìm thấy sản phẩm'
                    }
                }, status=status.HTTP_404_NOT_FOUND)

            cutoff_date = datetime.now() - timedelta(days=60)
            orders = Order.objects.filter(
                created_by=request.user,
                created_at__gte=cutoff_date,
                status='paid'
            )

            sales_history = []
            for order in orders:
                items = OrderItem.objects.filter(
                    order=order
                ).select_related('product')

                for item in items:
                    if item.product and item.product.id:
                        try:
                            sales_history.append({
                                'product_id': item.product.id,
                                'quantity': item.quantity,
                                'total_amount': float(item.quantity * item.unit_price),
                                'created_at': order.created_at.isoformat()
                            })
                        except (ValueError, TypeError) as e:
                            print(f"Error processing order item: {str(e)}")
                            continue

            predictions = ai_forecast_service.predict_demand(
                product_id=product.id,
                current_stock=product.stock_quantity,
                sales_history=sales_history,
                days_ahead=30
            )

            recommendation = ai_forecast_service.calculate_reorder_recommendation(
                product_id=product.id,
                current_stock=product.stock_quantity,
                predictions=predictions,
                lead_time_days=7
            )

            return Response({
                'status': '1',
                'response': {
                    'product': {
                        'id': product.id,
                        'name': product.name,
                        'sku': product.sku,
                        'current_stock': product.stock_quantity,
                        'unit': product.unit
                    },
                    'predictions': predictions,
                    'recommendation': recommendation
                }
            }, status=status.HTTP_200_OK)

        except Exception as ex:
            import traceback
            error_trace = traceback.format_exc()
            print(f"Product forecast error: {error_trace}")

            return Response({
                'status': '2',
                'response': {
                    'error_code': '9999',
                    'error_message_vn': f'Lỗi hệ thống: {str(ex)}',
                    'error_details': error_trace if request.user.is_staff else None
                }
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
