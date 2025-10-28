from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from django.utils.timezone import now
from ..models import Customer, Debit
from decimal import Decimal
from .serializer import PayDebitSerializer


class PayDebit(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        try:
            serializer = PayDebitSerializer(data=request.data)

            if serializer.is_valid():
                customer_code = serializer.validated_data['customer_code']
                payment_amount = serializer.validated_data['paid_amount']
                note = serializer.validated_data.get('note', '')

                try:
                    customer = Customer.objects.get(
                        customer_code=customer_code,
                        is_active=True
                    )
                except Customer.DoesNotExist:
                    return Response({
                        "status": "9999",
                        "error_message": "Khách hàng không tồn tại"
                    }, status=status.HTTP_404_NOT_FOUND)

                debit = Debit.objects.filter(
                    customer=customer,
                    is_active=True
                ).first()

                if not debit:
                    return Response({
                        "status": "9999",
                        "error_message": "Khách hàng không có nợ"
                    }, status=status.HTTP_404_NOT_FOUND)

                remaining_before = debit.debit_amount - debit.paid_amount

                if payment_amount > remaining_before:
                    return Response({
                        "status": "9999",
                        "error_message": f"Số tiền trả vượt quá số nợ. Nợ còn lại: {float(remaining_before)}"
                    }, status=status.HTTP_400_BAD_REQUEST)

                debit.paid_amount += payment_amount

                remaining_after = debit.debit_amount - debit.paid_amount

                if note:
                    debit.note = note if not debit.note else f"{debit.note}\n{note}"

                debit.save()
                if remaining_after == 0:
                    debt_status = "paid_debt"
                    status_message = "Đã trả hết nợ"
                else:
                    today = now().date()
                    if debit.due_date and debit.due_date < today:
                        debt_status = "overdue"
                        status_message = "Nợ quá hạn"
                    else:
                        debt_status = "in_debt"
                        status_message = "Còn nợ"

                response_data = {
                    "id": debit.id,
                    "customer_code": customer.customer_code,
                    "customer_name": customer.name,
                    "debit_amount": float(debit.debit_amount),
                    "paid_amount": float(debit.paid_amount),
                    "remaining_amount": float(remaining_after),
                    "payment_amount": float(payment_amount),
                    "total_amount": float(debit.total_amount),
                    "due_date": debit.due_date,
                    "debt_status": debt_status,
                    "status_message": status_message,
                    "note": debit.note,
                    "updated_at": debit.updated_at
                }

                return Response({
                    "status": "1",
                    "response": response_data
                }, status=status.HTTP_200_OK)
            else:
                return Response({
                    "status": "9999",
                    "error_message": "Dữ liệu không hợp lệ",
                    "errors": serializer.errors
                }, status=status.HTTP_400_BAD_REQUEST)

        except Exception as e:
            return Response({
                "status": "9999",
                "error_message": f"System error: {str(e)}"
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
