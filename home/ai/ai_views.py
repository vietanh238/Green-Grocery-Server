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

            sales_history = []
            for order in orders:
                order_items = OrderItem.objects.filter(
                    order=order).select_related('product')
                for item in order_items:
                    sales_history.append({
                        'product_id': item.product.id,
                        'quantity': item.quantity,
                        'total_amount': float(item.quantity * item.unit_price),
                        'created_at': order.created_at.isoformat()
                    })

            if len(sales_history) < 5:
                return Response({
                    'status': '2',
                    'response': {
                        'error_code': '001',
                        'error_message_vn': f'Cần ít nhất 5 giao dịch để train AI. Hiện tại có {len(sales_history)} giao dịch.',
                        'suggestion': 'Hãy tích lũy thêm dữ liệu bán hàng. Lý tưởng nhất là có dữ liệu từ nhiều ngày khác nhau để AI học được pattern theo thời gian.'
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
                        'products_analyzed': len(set(s['product_id'] for s in sales_history))
                    }
                }, status=status.HTTP_200_OK)
            else:
                return Response({
                    'status': '2',
                    'response': {
                        'error_message_vn': 'Không đủ dữ liệu để train AI'
                    }
                }, status=status.HTTP_400_BAD_REQUEST)

        except Exception as ex:
            return Response({
                'status': '2',
                'response': {
                    'error_code': '9999',
                    'error_message_vn': f'Lỗi hệ thống: {str(ex)}'
                }
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class GetReorderRecommendationsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            products = Product.objects.filter(created_by=request.user, is_active=True)

            cutoff_date = datetime.now() - timedelta(days=60)
            orders = Order.objects.filter(
                created_by=request.user,
                created_at__gte=cutoff_date,
                status='paid'
            )

            all_sales = []
            for order in orders:
                items = OrderItem.objects.filter(
                    order=order).select_related('product')
                for item in items:
                    all_sales.append({
                        'product_id': item.product.id,
                        'quantity': item.quantity,
                        'total_amount': float(item.quantity * item.unit_price),
                        'created_at': order.created_at.isoformat()
                    })

            recommendations = []

            for product in products:
                product_sales = [
                    s for s in all_sales if s['product_id'] == product.id]

                # Giảm yêu cầu xuống 1 giao dịch per product
                if len(product_sales) < 1:
                    continue

                predictions = ai_forecast_service.predict_demand(
                    product_id=product.id,
                    current_stock=product.stock_quantity,
                    sales_history=all_sales,
                    days_ahead=30
                )

                recommendation = ai_forecast_service.calculate_reorder_recommendation(
                    product_id=product.id,
                    current_stock=product.stock_quantity,
                    predictions=predictions,
                    lead_time_days=7
                )

                if recommendation and recommendation['should_reorder']:
                    recommendation['product_name'] = product.name
                    recommendation['product_sku'] = product.sku
                    recommendation['product_image'] = product.image if hasattr(
                        product, 'image') else ''
                    recommendation['unit'] = product.unit
                    recommendation['cost_price'] = float(product.cost_price)
                    recommendation['estimated_cost'] = round(
                        recommendation['optimal_order_quantity'] *
                        float(product.cost_price),
                        2
                    )
                    recommendations.append(recommendation)

            recommendations.sort(key=lambda x: (
                0 if x['urgency'] == 'high' else 1 if x['urgency'] == 'medium' else 2,
                x['days_until_stockout']
            ))

            total_estimated_cost = sum(r['estimated_cost']
                                       for r in recommendations)

            return Response({
                'status': '1',
                'response': {
                    'recommendations': recommendations,
                    'summary': {
                        'total_products_need_reorder': len(recommendations),
                        'high_urgency': len([r for r in recommendations if r['urgency'] == 'high']),
                        'medium_urgency': len([r for r in recommendations if r['urgency'] == 'medium']),
                        'low_urgency': len([r for r in recommendations if r['urgency'] == 'low']),
                        'total_estimated_cost': total_estimated_cost
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
                    order=order).select_related('product')
                for item in items:
                    sales_history.append({
                        'product_id': item.product.id,
                        'quantity': item.quantity,
                        'total_amount': float(item.quantity * item.unit_price),
                        'created_at': order.created_at.isoformat()
                    })

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
            return Response({
                'status': '2',
                'response': {
                    'error_code': '9999',
                    'error_message_vn': f'Lỗi hệ thống: {str(ex)}'
                }
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
