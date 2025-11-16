from django.db.models import Sum, Count, Q
from django.utils.timezone import now
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView
from rest_framework.response import Response
from core.models import Debt
from django.db import models

class GetDebtViews(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            total_debt = Debt.objects.aggregate(
                total=Sum("Debt_amount") - Sum("paid_amount")
            )["total"] or 0

            today = now().date()
            last_month_qs = Debt.objects.filter(
                created_at__month=today.month - 1,
                created_at__year=today.year
            ).aggregate(
                total=Sum("Debt_amount") - Sum("paid_amount")
            )
            last_month_total = last_month_qs["total"] or 0

            change_percent = 0
            if last_month_total > 0:
                change_percent = (
                    total_debt - last_month_total) / last_month_total * 100

            customer_count = Debt.objects.values(
                "customer").distinct().count()

            overdue_qs = Debt.objects.filter(
                due_date__lt=today,
                Debt_amount__gt=models.F("paid_amount")
            )
            overdue_amount = overdue_qs.aggregate(
                total=Sum("Debt_amount") - Sum("paid_amount")
            )["total"] or 0
            overdue_customers = overdue_qs.values(
                "customer").distinct().count()

            this_month_qs = Debt.objects.filter(
                created_at__month=today.month,
                created_at__year=today.year
            )
            this_month_amount = this_month_qs.aggregate(
                total=Sum("Debt_amount") - Sum("paid_amount")
            )["total"] or 0
            this_month_transactions = this_month_qs.count()

            return Response({
                "status": "1",
                "response": {
                    "total_debt": total_debt,
                    "change_percent": change_percent,
                    "customer_count": customer_count,
                    "Debt_overdue": {
                        "overdue_amount": overdue_amount,
                        "overdue_customers": overdue_customers,
                    },
                    "Debt_this_month": {
                        "this_month_amount": this_month_amount,
                        "this_month_transactions": this_month_transactions,
                    }
                }
            })

        except Exception as e:
            return Response({
                "status": "9999",
                "error_message": str(e) or "System error"
            })
