from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from django.utils.timezone import now
from core.models import Customer, Debt, DebtPayment
from decimal import Decimal
import uuid
from .serializer import PayDebitSerializer
from django.db.models import F, Sum


class PayDebit(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        try:
            serializer = PayDebitSerializer(data=request.data)

            if serializer.is_valid():
                customer_code = serializer.validated_data['customer_code']
                payment_amount = Decimal(
                    str(serializer.validated_data['paid_amount']))
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

                debts = Debt.objects.filter(
                    customer=customer,
                    debt_amount__gt=F("paid_amount"),
                    is_active=True
                ).order_by('due_date')

                if not debts.exists():
                    return Response({
                        "status": "9999",
                        "error_message": "Khách hàng không có nợ"
                    }, status=status.HTTP_404_NOT_FOUND)

                total_remaining_before = debts.aggregate(
                    total=Sum("debt_amount") - Sum("paid_amount")
                )["total"] or 0

                if payment_amount > total_remaining_before:
                    return Response({
                        "status": "9999",
                        "error_message": f"Số tiền trả vượt quá số nợ. Nợ còn lại: {float(total_remaining_before)}"
                    }, status=status.HTTP_400_BAD_REQUEST)

                remaining_payment = payment_amount
                processed_debts = []

                for debt in debts:
                    if remaining_payment <= 0:
                        break

                    remaining_debt = debt.debt_amount - debt.paid_amount
                    payment_for_this_debt = min(
                        remaining_payment, remaining_debt)

                    debt.paid_amount += payment_for_this_debt

                    if debt.paid_amount >= debt.debt_amount:
                        debt.status = 'paid'
                        debt.paid_at = now()
                    elif debt.paid_amount > 0:
                        debt.status = 'partial'
                    else:
                        debt.status = 'active'

                    if debt.due_date < now().date() and debt.status != 'paid':
                        debt.status = 'overdue'

                    debt.save()

                    DebtPayment.objects.create(
                        payment_code=f"PAY_{uuid.uuid4().hex[:16].upper()}",
                        debt=debt,
                        amount=payment_for_this_debt,
                        note=note,
                        created_by=request.user
                    )

                    processed_debts.append({
                        'debt_code': debt.debt_code,
                        'payment_amount': float(payment_for_this_debt),
                        'remaining_after': float(debt.debt_amount - debt.paid_amount)
                    })

                    remaining_payment -= payment_for_this_debt

                total_remaining_after = debts.aggregate(
                    total=Sum("debt_amount") - Sum("paid_amount")
                )["total"] or 0

                if total_remaining_after == 0:
                    debt_status = "paid_debt"
                    status_message = "Đã trả hết nợ"
                else:
                    has_overdue = Debt.objects.filter(
                        customer=customer,
                        due_date__lt=now().date(),
                        debt_amount__gt=F("paid_amount"),
                        is_active=True
                    ).exists()
                    debt_status = "overdue" if has_overdue else "in_debt"
                    status_message = "Nợ quá hạn" if has_overdue else "Còn nợ"

                customer.total_debt = total_remaining_after
                customer.save()

                response_data = {
                    "customer_code": customer.customer_code,
                    "customer_name": customer.name,
                    "payment_amount": float(payment_amount),
                    "remaining_before": float(total_remaining_before),
                    "remaining_after": float(total_remaining_after),
                    "debt_status": debt_status,
                    "status_message": status_message,
                    "note": note,
                    "processed_debts": processed_debts,
                    "updated_at": now().isoformat()
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
