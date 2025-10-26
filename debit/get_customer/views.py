from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from ..models import Customer
from ..models import Debit
from django.db.models import Sum, Max, F, ExpressionWrapper, DecimalField, When, Case, Value, CharField, Q, BooleanField
from django.utils.timezone import now


class GetCustomerView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            today = now().date()
            queryset = (
                Customer.objects
                .annotate(
                    total_debt=Sum(
                        ExpressionWrapper(
                            F("debit__debit_amount") - F("debit__paid_amount"),
                            output_field=DecimalField(
                                max_digits=19, decimal_places=5)
                        )
                    ),
                    last_transaction=Max("debit__created_at"),
                    is_over_due=Case(
                        When(
                            Q(debit__due_date__lt=today) & Q(
                                total_debt__gt=0),
                            then=Value(True)
                        ),
                        default=Value(False),
                        output_field=BooleanField()
                    ),
                    status=Case(
                        When(
                            Q(total_debt__gt=0) &
                            Q(is_over_due=False),
                            then=Value("in_debt")
                        ),
                        When(is_over_due=True, then=Value("overdue")),
                        When(debit__paid_amount=F("total_debt"), then=Value("paid_debt")),
                        default=Value("no_debt"),
                        output_field=CharField()
                    )
                )
                .filter(is_active=True)
                .values(
                    "customer_code",
                    "name",
                    "phone",
                    "address",
                    "total_debt",
                    "last_transaction",
                    "status"
                )
                .order_by("created_at")[:100]
            )

            return Response({
                "status": "1",
                "response": list(queryset)
            })

        except Exception:
            return Response({
                "status": "9999",
                "error_message": "System error"
            })
