from django.db.models import Sum, Count, Q, F
from django.utils.timezone import now
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView
from rest_framework.response import Response
from core.models import Debt, Customer
from django.db import models
from datetime import timedelta
from decimal import Decimal


class GetDebtViews(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            total_debt_result = Debt.objects.filter(
                is_active=True,
                debt_amount__gt=F("paid_amount")
            ).aggregate(
                total_debt=Sum("debt_amount") - Sum("paid_amount")
            )
            total_debt = total_debt_result["total_debt"] or 0

            today = now().date()

            first_day_of_month = today.replace(day=1)
            last_month_end = first_day_of_month - timedelta(days=1)
            last_month_start = last_month_end.replace(day=1)

            last_month_qs = Debt.objects.filter(
                created_at__date__gte=last_month_start,
                created_at__date__lte=last_month_end,
                is_active=True
            ).aggregate(
                total=Sum("debt_amount") - Sum("paid_amount")
            )
            last_month_total = last_month_qs["total"] or 0

            change_percent = 0
            if last_month_total > 0:
                change_percent = (
                    (total_debt - last_month_total) / last_month_total) * 100
            elif total_debt > 0 and last_month_total == 0:
                change_percent = 100

            customer_count = Debt.objects.filter(
                debt_amount__gt=F("paid_amount"),
                is_active=True
            ).values("customer").distinct().count()

            overdue_qs = Debt.objects.filter(
                due_date__lt=today,
                debt_amount__gt=F("paid_amount"),
                is_active=True
            )
            overdue_amount = overdue_qs.aggregate(
                total=Sum("debt_amount") - Sum("paid_amount")
            )["total"] or 0
            overdue_customers = overdue_qs.values(
                "customer").distinct().count()

            this_month_qs = Debt.objects.filter(
                created_at__year=today.year,
                created_at__month=today.month,
                is_active=True
            )
            this_month_amount = this_month_qs.aggregate(
                total=Sum("debt_amount") - Sum("paid_amount")
            )["total"] or 0
            this_month_transactions = this_month_qs.count()

            return Response({
                "status": "1",
                "response": {
                    "total_debt": float(total_debt),
                    "change_percent": round(change_percent, 2),
                    "customer_count": customer_count,
                    "debt_overdue": {
                        "overdue_amount": float(overdue_amount),
                        "overdue_customers": overdue_customers,
                    },
                    "debt_this_month": {
                        "this_month_amount": float(this_month_amount),
                        "this_month_transactions": this_month_transactions,
                    }
                }
            })

        except Exception as e:
            return Response({
                "status": "9999",
                "error_message": str(e) or "System error"
            })
