from decimal import Decimal

from django.db import transaction
from django.db.models import Sum
from rest_framework import status, viewsets
from rest_framework.decorators import api_view
from rest_framework.response import Response

from .models import (
    Account,
    AccountLimit,
    Category,
    ExchangeRate,
    Movement,
    Service,
    User,
)
from .serializers import (
    AccountLimitSerializer,
    AccountSerializer,
    CategorySerializer,
    ExchangeRateSerializer,
    MovementSerializer,
    ServiceSerializer,
    UserSerializer,
)


class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer


class CategoryViewSet(viewsets.ModelViewSet):
    queryset = Category.objects.select_related("id_user").all()
    serializer_class = CategorySerializer


class AccountViewSet(viewsets.ModelViewSet):
    queryset = Account.objects.select_related("id_user", "id_main_category").all()
    serializer_class = AccountSerializer


class ServiceViewSet(viewsets.ModelViewSet):
    queryset = Service.objects.select_related("id_user").all()
    serializer_class = ServiceSerializer


class ExchangeRateViewSet(viewsets.ModelViewSet):
    queryset = ExchangeRate.objects.all()
    serializer_class = ExchangeRateSerializer


class AccountLimitViewSet(viewsets.ModelViewSet):
    queryset = AccountLimit.objects.select_related("id_account").all()
    serializer_class = AccountLimitSerializer


class MovementViewSet(viewsets.ModelViewSet):
    queryset = Movement.objects.select_related(
        "id_account",
        "id_destination_account",
        "id_category",
        "id_service",
        "id_exchange_rate",
    ).all()
    serializer_class = MovementSerializer

    def create(self, request, *args, **kwargs):
        data = request.data
        destination_id = data.get("id_destination_account")

        if destination_id:
            required = [
                "id_account",
                "id_category",
                "amount",
                "movement_date",
                "original_currency",
            ]
            missing = [field for field in required if not data.get(field)]

            if missing:
                return Response(
                    {"error": "Faltan campos obligatorios", "fields": missing},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            try:
                amount = Decimal(str(data.get("amount")))
            except Exception:
                return Response(
                    {"error": "Monto inválido"},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            with transaction.atomic():
                last_group = (
                    Movement.objects.order_by("-transfer_group_id")
                    .values_list("transfer_group_id", flat=True)
                    .first()
                    or 0
                )
                group_id = int(last_group) + 1

                common = {
                    "id_category_id": data.get("id_category"),
                    "id_service_id": data.get("id_service") or None,
                    "id_exchange_rate_id": data.get("id_exchange_rate") or None,
                    "transfer_group_id": group_id,
                    "original_currency": data.get("original_currency"),
                    "movement_date": data.get("movement_date"),
                }

                salida = Movement.objects.create(
                    id_account_id=data.get("id_account"),
                    id_destination_account_id=destination_id,
                    amount=-abs(amount),
                    description=data.get("description") or "Transferencia enviada",
                    **common,
                )

                entrada = Movement.objects.create(
                    id_account_id=destination_id,
                    id_destination_account_id=data.get("id_account"),
                    amount=abs(amount),
                    description="Transferencia recibida",
                    **common,
                )

                return Response(
                    {
                        "message": "Transferencia creada",
                        "salida": MovementSerializer(salida).data,
                        "entrada": MovementSerializer(entrada).data,
                    },
                    status=status.HTTP_201_CREATED,
                )

        return super().create(request, *args, **kwargs)


@api_view(["GET"])
def dashboard(request):
    total_users = User.objects.count()
    total_accounts = Account.objects.count()
    income = Movement.objects.filter(amount__gt=0).aggregate(total=Sum("amount"))["total"] or 0
    expenses = Movement.objects.filter(amount__lt=0).aggregate(total=Sum("amount"))["total"] or 0
    balance = income + expenses

    return Response(
        {
            "total_users": total_users,
            "total_accounts": total_accounts,
            "income": income,
            "expenses": abs(expenses),
            "balance": balance,
        }
    )
