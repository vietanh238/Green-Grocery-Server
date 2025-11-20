from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from django.db import transaction
from django.utils import timezone
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from decouple import config

from core.models import Payment, Order, OrderItem, Product
from ..services import create_payment_request, delete_payment
from ..serializers import CreatePaymentSerializer, PaymentDetailSerializer

CHECKSUM_KEY = config("PAYOS_CHECKSUM_KEY")


class CreatePaymentView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        try:
            serializer = CreatePaymentSerializer(data=request.data)

            if not serializer.is_valid():
                return Response({
                    'status': '2',
                    'response': {
                        'error_code': '001',
                        'error_message_us': 'Validation error',
                        'error_message_vn': 'Dữ liệu không hợp lệ',
                        'errors': serializer.errors
                    }
                }, status=status.HTTP_400_BAD_REQUEST)

            data = serializer.validated_data
            order_code = str(data['orderCode'])
            amount = data['amount']
            description = data.get(
                'description', f'Thanh toán đơn hàng {order_code}')
            return_url = data['returnUrl']
            cancel_url = data['cancelUrl']
            items_data = data['items']
            buyer_name = data.get('buyerName', '')
            buyer_phone = data.get('buyerPhone', '')

            with transaction.atomic():
                if Payment.objects.filter(order_code=order_code).exists():
                    return Response({
                        'status': '2',
                        'response': {
                            'error_code': '002',
                            'error_message_us': 'Order already exists',
                            'error_message_vn': f'Đơn hàng {order_code} đã tồn tại'
                        }
                    }, status=status.HTTP_400_BAD_REQUEST)

                subtotal = sum(item['total_price'] for item in items_data)

                order = Order.objects.create(
                    order_code=order_code,
                    user=request.user if request.user.is_authenticated else None,
                    status='pending',
                    subtotal=subtotal,
                    total_amount=amount,
                    payment_method='qr',
                    buyer_name=buyer_name,
                    buyer_phone=buyer_phone,
                    created_by=request.user if request.user.is_authenticated else None,
                    updated_by=request.user if request.user.is_authenticated else None
                )

                order_items = []
                for item_data in items_data:
                    try:
                        product = Product.objects.get(
                            bar_code=item_data['bar_code'],
                            is_active=True
                        )

                        if product.stock_quantity < item_data['quantity']:
                            raise ValueError(
                                f"Sản phẩm {product.name} không đủ số lượng trong kho")

                        order_item = OrderItem(
                            order=order,
                            product=product,
                            product_name=item_data['name'],
                            product_sku=item_data['sku'],
                            quantity=item_data['quantity'],
                            unit_price=item_data['unit_price'],
                            total_price=item_data['total_price'],
                            cost_price=product.cost_price,
                            created_by=request.user if request.user.is_authenticated else None,
                            updated_by=request.user if request.user.is_authenticated else None
                        )
                        order_items.append(order_item)

                    except Product.DoesNotExist:
                        order_item = OrderItem(
                            order=order,
                            product=None,
                            product_name=item_data['name'],
                            product_sku=item_data['sku'],
                            quantity=item_data['quantity'],
                            unit_price=item_data['unit_price'],
                            total_price=item_data['total_price'],
                            cost_price=0,
                            created_by=request.user if request.user.is_authenticated else None,
                            updated_by=request.user if request.user.is_authenticated else None
                        )
                        order_items.append(order_item)

                OrderItem.objects.bulk_create(order_items)

                try:
                    payos_buyer = None
                    if buyer_name or buyer_phone:
                        payos_buyer = {
                            "name": buyer_name,
                            "phone": buyer_phone,
                            "email": ""
                        }

                    payos_res = create_payment_request(
                        order_code=order_code,
                        amount=int(amount),
                        description=description,
                        return_url=return_url,
                        cancel_url=cancel_url,
                        buyer=payos_buyer
                    )
                except Exception as e:
                    return Response({
                        'status': '2',
                        'response': {
                            'error_code': '003',
                            'error_message_us': f'PayOS error: {str(e)}',
                            'error_message_vn': f'Lỗi kết nối PayOS: {str(e)}'
                        }
                    }, status=status.HTTP_502_BAD_GATEWAY)

                payos_data = payos_res.get("data", {})
                transaction_id = payos_data.get("paymentLinkId")
                checkout_url = payos_data.get("checkoutUrl")
                qr_code = payos_data.get("qrCode")

                payment = Payment.objects.create(
                    order=order,
                    order_code=order_code,
                    transaction_id=transaction_id,
                    payment_method='qr',
                    amount=amount,
                    paid_amount=0,
                    status='pending',
                    description=description,
                    qr_code_url=qr_code,
                    checkout_url=checkout_url,
                    created_by=request.user if request.user.is_authenticated else None,
                    updated_by=request.user if request.user.is_authenticated else None
                )

                return Response({
                    'status': '1',
                    'response': {
                        "orderCode": order_code,
                        "amount": float(amount),
                        "transactionId": transaction_id,
                        "checkoutUrl": checkout_url,
                        "qrCode": qr_code,
                        "message": "Tạo đơn hàng thành công"
                    }
                }, status=status.HTTP_201_CREATED)

        except Exception as ex:
            return Response({
                'status': '2',
                'response': {
                    'error_code': '9999',
                    'error_message_us': 'An internal server error occurred.',
                    'error_message_vn': f'Lỗi hệ thống: {str(ex)}'
                }
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def delete(self, request, pk):
        try:
            order_code = pk

            if not order_code:
                return Response({
                    'status': '2',
                    'response': {
                        'error_code': '001',
                        'error_message_us': 'Invalid order code',
                        'error_message_vn': 'Mã đơn hàng không hợp lệ'
                    }
                }, status=status.HTTP_400_BAD_REQUEST)

            with transaction.atomic():
                try:
                    payment = Payment.objects.select_related('order').get(
                        order_code=order_code
                    )
                except Payment.DoesNotExist:
                    return Response({
                        'status': '2',
                        'response': {
                            'error_code': '002',
                            'error_message_us': 'Payment not found',
                            'error_message_vn': 'Không tìm thấy thanh toán'
                        }
                    }, status=status.HTTP_404_NOT_FOUND)

                if payment.status == 'paid':
                    return Response({
                        'status': '2',
                        'response': {
                            'error_code': '003',
                            'error_message_us': 'Cannot cancel paid order',
                            'error_message_vn': 'Không thể hủy đơn hàng đã thanh toán'
                        }
                    }, status=status.HTTP_400_BAD_REQUEST)

                try:
                    payos_res = delete_payment(order_code)
                    if payos_res.get('code') != '00':
                        return Response({
                            'status': '2',
                            'response': {
                                'error_code': '004',
                                'error_message_us': 'PayOS cancellation failed',
                                'error_message_vn': 'Không thể hủy thanh toán trên PayOS'
                            }
                        }, status=status.HTTP_400_BAD_REQUEST)
                except Exception as e:
                    return Response({
                        'status': '2',
                        'response': {
                            'error_code': '005',
                            'error_message_us': f'PayOS error: {str(e)}',
                            'error_message_vn': f'Lỗi PayOS: {str(e)}'
                        }
                    }, status=status.HTTP_502_BAD_GATEWAY)

                payment.status = 'cancelled'
                payment.cancelled_at = timezone.now()
                payment.updated_by = request.user if request.user.is_authenticated else None
                payment.save()

                if payment.order:
                    payment.order.status = 'cancelled'
                    payment.order.cancelled_at = timezone.now()
                    payment.order.updated_by = request.user if request.user.is_authenticated else None
                    payment.order.save()

                return Response({
                    'status': '1',
                    'response': {
                        "order_code": order_code,
                        "message": "Hủy đơn hàng thành công"
                    }
                }, status=status.HTTP_200_OK)

        except Exception as ex:
            return Response({
                'status': '2',
                'response': {
                    'error_code': '9999',
                    'error_message_us': 'An internal server error occurred.',
                    'error_message_vn': f'Lỗi hệ thống: {str(ex)}'
                }
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
