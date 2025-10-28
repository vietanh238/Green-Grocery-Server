from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from django.db.models import Sum, F, ExpressionWrapper, DecimalField
from django.utils.timezone import now
from ..models import Customer, Debit
from decimal import Decimal
from .serializer import CreateDebitSerializer


class CreateDebit(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        try:
            serializer = CreateDebitSerializer(data=request.data)

            if serializer.is_valid():
                customer_code = serializer.validated_data['customer_code']
                new_debit_amount = serializer.validated_data['debit_amount']
                due_date = serializer.validated_data['due_date']
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

                existing_debit = Debit.objects.filter(
                    customer=customer,
                    is_active=True
                ).first()

                if existing_debit:
                    existing_debit.debit_amount += new_debit_amount
                    existing_debit.total_amount = existing_debit.debit_amount
                    existing_debit.due_date = due_date

                    if note:
                        existing_debit.note = note if not existing_debit.note else f"{existing_debit.note}\n{note}"

                    existing_debit.save()

                    response_data = {
                        "id": existing_debit.id,
                        "customer_code": customer.customer_code,
                        "customer_name": customer.name,
                        "debit_amount": float(existing_debit.debit_amount),
                        "paid_amount": float(existing_debit.paid_amount),
                        "total_amount": float(existing_debit.total_amount),
                        "due_date": existing_debit.due_date,
                        "note": existing_debit.note,
                        "created_at": existing_debit.created_at,
                        "updated_at": existing_debit.updated_at,
                        "message": "Cập nhật nợ thành công"
                    }
                else:
                    new_debit = Debit.objects.create(
                        customer=customer,
                        debit_amount=new_debit_amount,
                        paid_amount=Decimal('0.00000'),
                        total_amount=new_debit_amount,
                        due_date=due_date,
                        note=note
                    )

                    response_data = {
                        "id": new_debit.id,
                        "customer_code": customer.customer_code,
                        "customer_name": customer.name,
                        "debit_amount": float(new_debit.debit_amount),
                        "paid_amount": float(new_debit.paid_amount),
                        "total_amount": float(new_debit.total_amount),
                        "due_date": new_debit.due_date,
                        "note": new_debit.note,
                        "created_at": new_debit.created_at,
                        "updated_at": new_debit.updated_at,
                        "message": "Ghi nợ thành công"
                    }

                return Response({
                    "status": "1",
                    "response": response_data
                }, status=status.HTTP_201_CREATED)
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
