from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from django.db import transaction
from django.db.models import Sum, Q, F
import json
import uuid
from product.models import Product
from ..models import Customer, Debit
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync


class CreateDebitView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        try:
            customer_name = request.data.get('customer_name')
            customer_phone = request.data.get('customer_phone')
            customer_address = request.data.get('customer_address', '')
            customer_code = request.data.get('customer_code')

            debit_amount = request.data.get('debit_amount')
            paid_amount = request.data.get('paid_amount', 0)
            total_amount = request.data.get('total_amount')
            due_date = request.data.get('due_date')
            note = request.data.get('note', '')
            items = request.data.get('items', [])

            if not debit_amount:
                return Response({
                    'status': '2',
                    'error_message': 'Thiếu số tiền ghi nợ'
                }, status=status.HTTP_400_BAD_REQUEST)

            with transaction.atomic():
                if customer_code:
                    try:
                        customer = Customer.objects.get(
                            customer_code=customer_code, is_active=True)
                    except Customer.DoesNotExist:
                        return Response({
                            'status': '2',
                            'error_message': 'Không tìm thấy khách hàng'
                        }, status=status.HTTP_404_NOT_FOUND)
                elif customer_phone:
                    customer = Customer.objects.filter(
                        phone=customer_phone,
                        is_active=True
                    ).first()

                    if not customer:
                        if not customer_name:
                            return Response({
                                'status': '2',
                                'error_message': 'Thiếu tên khách hàng'
                            }, status=status.HTTP_400_BAD_REQUEST)

                        customer = Customer.objects.create(
                            customer_code=str(uuid.uuid4()),
                            name=customer_name,
                            phone=customer_phone,
                            address=customer_address
                        )
                else:
                    return Response({
                        'status': '2',
                        'error_message': 'Thiếu thông tin khách hàng (customer_code hoặc customer_phone)'
                    }, status=status.HTTP_400_BAD_REQUEST)

                debit = Debit.objects.create(
                    customer=customer,
                    debit_amount=debit_amount,
                    paid_amount=paid_amount,
                    total_amount=total_amount,
                    due_date=due_date,
                    note=note
                )

                list_product_reorder = []

                for item in items:
                    bar_code = item.get('bar_code') or item.get('sku')
                    quantity = item.get('quantity', 0)

                    if bar_code:
                        try:
                            product = Product.objects.get(bar_code=bar_code)
                            product.stock_quantity = max(
                                0, product.stock_quantity - quantity)

                            if product.stock_quantity <= product.reorder_point:
                                list_product_reorder.append(product.bar_code)

                            product.save()
                        except Product.DoesNotExist:
                            pass

                channel_layer = get_channel_layer()
                async_to_sync(channel_layer.group_send)(
                    "broadcast",
                    {
                        "type": "debit_created",
                        "data": {
                            "customerName": customer.name,
                            "debitAmount": float(debit_amount),
                            "message": f"Đã ghi nợ {debit_amount}đ cho {customer.name}"
                        }
                    }
                )

                if list_product_reorder:
                    async_to_sync(channel_layer.group_send)(
                        "broadcast",
                        {
                            "type": "message",
                            "data": {
                                'message_type': 'remind_reorder',
                                "items": list_product_reorder,
                                "message": "Sản phẩm gần sắp hết"
                            }
                        }
                    )

                return Response({
                    'status': '1',
                    'response': {
                        'debit_id': debit.id,
                        'customer_code': customer.customer_code,
                        'customer_name': customer.name,
                        'customer_phone': customer.phone,
                        'debit_amount': float(debit.debit_amount),
                        'paid_amount': float(debit.paid_amount),
                        'total_amount': float(debit.total_amount),
                        'due_date': debit.due_date,
                        'note': debit.note,
                        'created_at': debit.created_at.isoformat()
                    }
                }, status=status.HTTP_201_CREATED)

        except Exception as e:
            return Response({
                'status': '9999',
                'error_message': f'Lỗi hệ thống: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
