from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from core.models import Customer, Debt
from django.db.models import Subquery, OuterRef, Case, When, Value, CharField, Prefetch
from django.utils.timezone import now
from django.db import models


class GetCustomerView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            today = now().date()

            last_due_date_subquery = Debt.objects.filter(
                customer_id=OuterRef('id'),
                status__in=['active', 'partial', 'overdue']
            ).order_by('-due_date').values('due_date')[:1]

            last_transaction_subquery = Debt.objects.filter(
                customer_id=OuterRef('id')
            ).order_by('-created_at').values('created_at')[:1]

            customers = (
                Customer.objects
                .filter(is_active=True)
                .annotate(
                    due_date=Subquery(last_due_date_subquery),
                    last_transaction_date=Subquery(last_transaction_subquery),
                    debt_status=Case(
                        When(total_debt=0, then=Value('no_debt')),
                        When(due_date__lt=today, then=Value('overdue')),
                        When(due_date__gte=today, then=Value('active')),
                        default=Value('no_debt'),
                        output_field=CharField()
                    )
                )
                .prefetch_related(
                    Prefetch(
                        'debts',
                        queryset=Debt.objects.all().order_by(
                            '-created_at')[:5],
                        to_attr='recent_debts'
                    )
                )[:100]
            )

            customer_list = []
            for customer in customers:
                history = []
                for debt in customer.recent_debts:
                    history.append({
                        'date': debt.created_at.strftime('%d/%m/%Y'),
                        'amount': float(debt.debt_amount),
                        'note': debt.note or ''
                    })

                customer_data = {
                    "customer_code": customer.customer_code,
                    "name": customer.name,
                    "phone": customer.phone,
                    "address": customer.address,
                    "total_debt": float(customer.total_debt),
                    "due_date": customer.due_date.strftime('%d/%m/%Y') if customer.due_date else None,
                    "last_transaction_date": customer.last_transaction_date.strftime('%d/%m/%Y') if customer.last_transaction_date else None,
                    "debt_status": customer.debt_status,
                    "customer_type": customer.customer_type,
                    "total_orders": customer.total_orders,
                    "total_spent": float(customer.total_spent),
                    "last_purchase_date": customer.last_purchase_date.strftime('%d/%m/%Y') if customer.last_purchase_date else None,
                    "history": history
                }
                customer_list.append(customer_data)

            return Response({
                "status": "1",
                "response": customer_list
            })

        except Exception as e:
            return Response({
                "status": "2",
                "response": {
                    "error_code": "9999",
                    "error_message_us": "System error",
                    "error_message_vn": f"Lỗi hệ thống: {str(e)}"
                }
            })
