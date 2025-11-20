from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from django.db.models import Sum, Q, F
from django.db import models
from datetime import datetime, timedelta

from core.models import Product, InventoryTransaction
from core.services.inventory_service import InventoryService


class InventoryHistoryView(APIView):
    """Get inventory transaction history for a product"""
    permission_classes = [IsAuthenticated]

    def get(self, request, product_id):
        try:
            # Validate product exists
            try:
                product = Product.objects.get(id=product_id, is_active=True)
            except Product.DoesNotExist:
                return Response({
                    'status': '2',
                    'response': {
                        'error_code': '404',
                        'error_message_vn': 'Không tìm thấy sản phẩm'
                    }
                }, status=status.HTTP_404_NOT_FOUND)

            # Get query parameters
            limit = int(request.GET.get('limit', 50))
            transaction_type = request.GET.get('type', None)

            # Get transactions
            queryset = InventoryTransaction.objects.filter(
                product_id=product_id
            ).select_related('product', 'created_by')

            if transaction_type:
                queryset = queryset.filter(transaction_type=transaction_type)

            transactions = queryset.order_by('-created_at')[:limit]

            # Format response
            history = []
            for txn in transactions:
                history.append({
                    'id': txn.id,
                    'transaction_code': txn.transaction_code,
                    'transaction_type': txn.transaction_type,
                    'transaction_type_display': txn.get_transaction_type_display(),
                    'quantity': txn.quantity,
                    'quantity_before': txn.quantity_before,
                    'quantity_after': txn.quantity_after,
                    'unit_price': float(txn.unit_price),
                    'total_value': float(txn.total_value),
                    'reference_type': txn.reference_type,
                    'reference_id': txn.reference_id,
                    'note': txn.note,
                    'created_by': txn.created_by.username if txn.created_by else None,
                    'created_at': txn.created_at.isoformat(),
                })

            return Response({
                'status': '1',
                'response': {
                    'product': {
                        'id': product.id,
                        'name': product.name,
                        'sku': product.sku,
                        'current_stock': product.stock_quantity,
                        'unit': product.unit,
                    },
                    'history': history,
                    'count': len(history)
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


class InventoryAdjustmentView(APIView):
    """Adjust inventory stock (kiểm kê)"""
    permission_classes = [IsAuthenticated]

    def post(self, request):
        try:
            product_id = request.data.get('product_id')
            new_quantity = request.data.get('new_quantity')
            reason = request.data.get('reason', 'Điều chỉnh tồn kho')

            if not product_id or new_quantity is None:
                return Response({
                    'status': '2',
                    'response': {
                        'error_code': '001',
                        'error_message_vn': 'Thiếu thông tin bắt buộc'
                    }
                }, status=status.HTTP_400_BAD_REQUEST)

            try:
                new_quantity = int(new_quantity)
                if new_quantity < 0:
                    raise ValueError()
            except:
                return Response({
                    'status': '2',
                    'response': {
                        'error_code': '002',
                        'error_message_vn': 'Số lượng không hợp lệ'
                    }
                }, status=status.HTTP_400_BAD_REQUEST)

            # Adjust stock using InventoryService
            result = InventoryService.adjust_stock(
                product_id=product_id,
                new_quantity=new_quantity,
                reason=reason,
                created_by=request.user
            )

            return Response({
                'status': '1',
                'response': {
                    'message': 'Điều chỉnh tồn kho thành công',
                    'transaction_code': result['transaction'].transaction_code,
                    'product_name': result['product'].name,
                    'quantity_before': result['quantity_before'],
                    'quantity_after': result['quantity_after'],
                    'quantity_diff': result['quantity_diff']
                }
            }, status=status.HTTP_200_OK)

        except ValueError as ve:
            return Response({
                'status': '2',
                'response': {
                    'error_code': '003',
                    'error_message_vn': str(ve)
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


class InventoryDamageView(APIView):
    """Record damaged goods"""
    permission_classes = [IsAuthenticated]

    def post(self, request):
        try:
            product_id = request.data.get('product_id')
            quantity = request.data.get('quantity')
            reason = request.data.get('reason', 'Hàng hư hỏng')

            if not product_id or not quantity:
                return Response({
                    'status': '2',
                    'response': {
                        'error_code': '001',
                        'error_message_vn': 'Thiếu thông tin bắt buộc'
                    }
                }, status=status.HTTP_400_BAD_REQUEST)

            try:
                quantity = int(quantity)
                if quantity <= 0:
                    raise ValueError()
            except:
                return Response({
                    'status': '2',
                    'response': {
                        'error_code': '002',
                        'error_message_vn': 'Số lượng không hợp lệ'
                    }
                }, status=status.HTTP_400_BAD_REQUEST)

            # Record damage using InventoryService
            result = InventoryService.record_damage(
                product_id=product_id,
                quantity=quantity,
                reason=reason,
                created_by=request.user
            )

            return Response({
                'status': '1',
                'response': {
                    'message': 'Đã ghi nhận hàng hư hỏng',
                    'transaction_code': result['transaction'].transaction_code,
                    'product_name': result['product'].name,
                    'quantity': quantity,
                    'quantity_after': result['quantity_after']
                }
            }, status=status.HTTP_200_OK)

        except ValueError as ve:
            return Response({
                'status': '2',
                'response': {
                    'error_code': '003',
                    'error_message_vn': str(ve)
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


class InventoryLostView(APIView):
    """Record lost goods"""
    permission_classes = [IsAuthenticated]

    def post(self, request):
        try:
            product_id = request.data.get('product_id')
            quantity = request.data.get('quantity')
            reason = request.data.get('reason', 'Hàng mất')

            if not product_id or not quantity:
                return Response({
                    'status': '2',
                    'response': {
                        'error_code': '001',
                        'error_message_vn': 'Thiếu thông tin bắt buộc'
                    }
                }, status=status.HTTP_400_BAD_REQUEST)

            try:
                quantity = int(quantity)
                if quantity <= 0:
                    raise ValueError()
            except:
                return Response({
                    'status': '2',
                    'response': {
                        'error_code': '002',
                        'error_message_vn': 'Số lượng không hợp lệ'
                    }
                }, status=status.HTTP_400_BAD_REQUEST)

            # Record lost using InventoryService
            result = InventoryService.record_lost(
                product_id=product_id,
                quantity=quantity,
                reason=reason,
                created_by=request.user
            )

            return Response({
                'status': '1',
                'response': {
                    'message': 'Đã ghi nhận hàng mất',
                    'transaction_code': result['transaction'].transaction_code,
                    'product_name': result['product'].name,
                    'quantity': quantity,
                    'quantity_after': result['quantity_after']
                }
            }, status=status.HTTP_200_OK)

        except ValueError as ve:
            return Response({
                'status': '2',
                'response': {
                    'error_code': '003',
                    'error_message_vn': str(ve)
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


class InventoryReturnView(APIView):
    """Return goods to stock"""
    permission_classes = [IsAuthenticated]

    def post(self, request):
        try:
            product_id = request.data.get('product_id')
            quantity = request.data.get('quantity')
            unit_price = request.data.get('unit_price', 0)
            note = request.data.get('note', 'Trả hàng về kho')

            if not product_id or not quantity:
                return Response({
                    'status': '2',
                    'response': {
                        'error_code': '001',
                        'error_message_vn': 'Thiếu thông tin bắt buộc'
                    }
                }, status=status.HTTP_400_BAD_REQUEST)

            try:
                quantity = int(quantity)
                if quantity <= 0:
                    raise ValueError()
            except:
                return Response({
                    'status': '2',
                    'response': {
                        'error_code': '002',
                        'error_message_vn': 'Số lượng không hợp lệ'
                    }
                }, status=status.HTTP_400_BAD_REQUEST)

            # Return stock using InventoryService
            result = InventoryService.return_stock(
                product_id=product_id,
                quantity=quantity,
                unit_price=unit_price,
                reference_type='return',
                reference_id=None,
                note=note,
                created_by=request.user
            )

            return Response({
                'status': '1',
                'response': {
                    'message': 'Đã trả hàng về kho',
                    'transaction_code': result['transaction'].transaction_code,
                    'product_name': result['product'].name,
                    'quantity': quantity,
                    'quantity_after': result['quantity_after']
                }
            }, status=status.HTTP_200_OK)

        except ValueError as ve:
            return Response({
                'status': '2',
                'response': {
                    'error_code': '003',
                    'error_message_vn': str(ve)
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


class InventorySummaryView(APIView):
    """Get inventory summary and statistics"""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            # Get query parameters
            start_date_str = request.GET.get('start_date')
            end_date_str = request.GET.get('end_date')

            start_date = None
            end_date = None

            if start_date_str:
                start_date = datetime.fromisoformat(start_date_str.replace('Z', '+00:00'))
            if end_date_str:
                end_date = datetime.fromisoformat(end_date_str.replace('Z', '+00:00'))

            # Get summary from service
            summary = InventoryService.get_inventory_summary(start_date, end_date)

            # Get additional statistics
            products = Product.objects.filter(is_active=True, created_by=request.user)

            total_products = products.count()
            total_stock_value = sum(p.stock_value for p in products)
            low_stock_count = products.filter(
                stock_quantity__lte=F('reorder_point'),
                stock_quantity__gt=0
            ).count()
            out_of_stock_count = products.filter(stock_quantity=0).count()

            # Get recent transactions
            recent_transactions = InventoryTransaction.objects.filter(
                created_by=request.user
            ).select_related('product', 'created_by').order_by('-created_at')[:10]

            recent = []
            for txn in recent_transactions:
                recent.append({
                    'transaction_code': txn.transaction_code,
                    'transaction_type': txn.get_transaction_type_display(),
                    'product_name': txn.product.name if txn.product else 'N/A',
                    'quantity': txn.quantity,
                    'created_at': txn.created_at.isoformat()
                })

            return Response({
                'status': '1',
                'response': {
                    'summary': summary,
                    'statistics': {
                        'total_products': total_products,
                        'total_stock_value': float(total_stock_value),
                        'low_stock_count': low_stock_count,
                        'out_of_stock_count': out_of_stock_count,
                    },
                    'recent_transactions': recent
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

