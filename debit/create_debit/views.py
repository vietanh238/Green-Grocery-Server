from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from django.db import transaction
from django.db.models import F
from django.utils.timezone import now
from decimal import Decimal
import uuid
from .serializer import CreateDebitSerializer
from core.models import Customer, Debt


class CreateDebitView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = CreateDebitSerializer(data=request.data)
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

        try:
            validated_data = serializer.validated_data
            customer_code = validated_data['customer_code']
            debit_amount = validated_data['debit_amount']
            due_date = validated_data['due_date']
            note = validated_data.get('note', '')

            with transaction.atomic():
                try:
                    customer = Customer.objects.get(
                        customer_code=customer_code,
                        is_active=True
                    )
                except Customer.DoesNotExist:
                    return Response({
                        'status': '2',
                        'response': {
                            'error_code': '002',
                            'error_message_us': 'Customer not found',
                            'error_message_vn': 'Không tìm thấy khách hàng'
                        }
                    }, status=status.HTTP_404_NOT_FOUND)

                debt_code = f"DEBT_{uuid.uuid4().hex[:16].upper()}"

                debt = Debt.objects.create(
                    debt_code=debt_code,
                    customer=customer,
                    total_amount=debit_amount,
                    debt_amount=debit_amount,
                    paid_amount=0,
                    due_date=due_date,
                    status='active',
                    note=note
                )

                Customer.objects.filter(pk=customer.pk).update(
                    total_debt=F('total_debt') + Decimal(str(debit_amount))
                )

                customer.refresh_from_db()

                return Response({
                    'status': '1',
                    'response': {
                        'debt_id': debt.id,
                        'debt_code': debt.debt_code,
                        'customer_code': customer.customer_code,
                        'customer_name': customer.name,
                        'total_debt': float(customer.total_debt),
                        'debt_amount': float(debit_amount),
                        'due_date': debt.due_date.isoformat()
                    }
                }, status=status.HTTP_201_CREATED)

        except Exception as e:
            return Response({
                'status': '2',
                'response': {
                    'error_code': '9999',
                    'error_message_us': 'System error',
                    'error_message_vn': f'Lỗi hệ thống: {str(e)}'
                }
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
