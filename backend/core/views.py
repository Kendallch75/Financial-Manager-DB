from decimal import Decimal

from django.conf import settings
from django.contrib.auth.hashers import check_password, make_password
from django.db import transaction
from django.db.models import Sum
from django.utils import timezone
from datetime import datetime

from rest_framework import status, viewsets
from rest_framework.decorators import api_view
from rest_framework.response import Response

from .models import (
    User,
    Account,
    Category,
    Service,
    Movement,
    ExchangeRate,
    AccountLimit,
)
from .serializers import (
    UserSerializer,
    PublicUserSerializer,
    AccountSerializer,
    CategorySerializer,
    ServiceSerializer,
    MovementSerializer,
    ExchangeRateSerializer,
    AccountLimitSerializer,
)


def future_date():
    return timezone.make_aware(datetime(2099, 12, 31, 23, 59, 59))


def current_user(request):
    user_id = request.session.get("user_id")
    if not user_id:
        return None
    try:
        return User.objects.get(
            id_user=user_id,
            cancellation_date=future_date(),
        )
    except User.DoesNotExist:
        request.session.flush()
        return None


def require_login(request):
    user = current_user(request)
    if not user:
        return None, Response(
            {"detail": "Debe iniciar sesión."},
            status=status.HTTP_401_UNAUTHORIZED,
        )
    return user, None


@api_view(["POST"])
def login_view(request):
    email = (request.data.get("email") or "").strip().lower()
    password = request.data.get("password") or ""

    if not email or not password:
        return Response(
            {"detail": "Email y contraseña son obligatorios."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    try:
        user = User.objects.get(email=email, cancellation_date=future_date())
    except User.DoesNotExist:
        return Response(
            {"detail": "Credenciales inválidas."},
            status=status.HTTP_401_UNAUTHORIZED,
        )

    if not check_password(password, user.password_hash):
        return Response(
            {"detail": "Credenciales inválidas."},
            status=status.HTTP_401_UNAUTHORIZED,
        )

    request.session.flush()
    request.session["user_id"] = user.id_user
    request.session["user_email"] = user.email
    request.session.set_expiry(60 * 60 * 24 * 7)
    request.session.save()
    return Response({"user": PublicUserSerializer(user).data})


@api_view(["POST"])
def register_view(request):
    first_name = (request.data.get("first_name") or "").strip()
    last_name_1 = (request.data.get("last_name_1") or "").strip()
    last_name_2 = (request.data.get("last_name_2") or "").strip() or None
    email = (request.data.get("email") or "").strip().lower()
    password = request.data.get("password") or ""

    if not first_name or not last_name_1 or not email or not password:
        return Response(
            {
                "detail": "Nombre, primer apellido, email y contraseña son obligatorios."
            },
            status=status.HTTP_400_BAD_REQUEST,
        )

    if len(password) < 6:
        return Response(
            {"detail": "La contraseña debe tener al menos 6 caracteres."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    if User.objects.filter(email=email).exists():
        return Response(
            {"detail": "Ya existe una cuenta con ese email."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    user = User.objects.create(
        first_name=first_name,
        last_name_1=last_name_1,
        last_name_2=last_name_2,
        email=email,
        password_hash=make_password(password),
        password_hash_2=make_password(password + settings.SECRET_KEY),
    )

    create_default_user_data(user)
    request.session.flush()
    request.session["user_id"] = user.id_user
    request.session["user_email"] = user.email
    request.session.set_expiry(60 * 60 * 24 * 7)
    request.session.save()
    return Response({"user": PublicUserSerializer(user).data}, status=status.HTTP_201_CREATED)


@api_view(["POST"])
def logout_view(request):
    request.session.flush()
    return Response({"detail": "Sesión cerrada."})


@api_view(["GET"])
def me_view(request):
    user = current_user(request)
    if not user:
        return Response({"user": None}, status=status.HTTP_200_OK)
    return Response({"user": PublicUserSerializer(user).data})


def create_default_user_data(user):
    income = Category.objects.create(
        id_user=user,
        name="Salario",
        type="INCOME",
        description="Ingresos principales",
        color="#22c55e",
    )
    food = Category.objects.create(
        id_user=user,
        name="Alimentación",
        type="EXPENSE",
        description="Comidas, supermercado y restaurantes",
        color="#ef4444",
    )
    Category.objects.create(
        id_user=user,
        name="Transporte",
        type="EXPENSE",
        description="Bus, combustible, Uber o mantenimiento",
        color="#f97316",
    )
    account = Account.objects.create(
        id_user=user,
        account_name="Efectivo",
        account_type="ACTIVO",
        currency="CRC",
    )
    Movement.objects.create(
        id_account=account,
        id_category=income,
        amount=Decimal("0.00"),
        original_currency="CRC",
        description="Cuenta creada",
        movement_date=timezone.localdate(),
    )
    return food


class LoginRequiredViewSet(viewsets.ModelViewSet):
    def get_logged_user_or_raise(self):
        user = current_user(self.request)
        if not user:
            from rest_framework.exceptions import NotAuthenticated

            raise NotAuthenticated("Debe iniciar sesión.")
        return user


class UserViewSet(LoginRequiredViewSet):
    serializer_class = UserSerializer

    def get_queryset(self):
        user = self.get_logged_user_or_raise()
        return User.objects.filter(id_user=user.id_user)

    def perform_destroy(self, instance):
        instance.cancellation_date = timezone.now()
        instance.save()


class CategoryViewSet(LoginRequiredViewSet):
    serializer_class = CategorySerializer

    def get_queryset(self):
        user = self.get_logged_user_or_raise()
        return Category.objects.filter(id_user=user).order_by("name")

    def perform_create(self, serializer):
        serializer.save(id_user=self.get_logged_user_or_raise())


class AccountViewSet(LoginRequiredViewSet):
    serializer_class = AccountSerializer

    def get_queryset(self):
        user = self.get_logged_user_or_raise()
        return Account.objects.filter(id_user=user).order_by("account_name")

    def perform_create(self, serializer):
        serializer.save(id_user=self.get_logged_user_or_raise())


class ServiceViewSet(LoginRequiredViewSet):
    serializer_class = ServiceSerializer

    def get_queryset(self):
        user = self.get_logged_user_or_raise()
        return Service.objects.filter(id_user=user).order_by("due_day", "service_name")

    def perform_create(self, serializer):
        serializer.save(id_user=self.get_logged_user_or_raise())


class ExchangeRateViewSet(LoginRequiredViewSet):
    queryset = ExchangeRate.objects.all().order_by("-rate_date")
    serializer_class = ExchangeRateSerializer

    def get_queryset(self):
        self.get_logged_user_or_raise()
        return super().get_queryset()


class AccountLimitViewSet(LoginRequiredViewSet):
    serializer_class = AccountLimitSerializer

    def get_queryset(self):
        user = self.get_logged_user_or_raise()
        return AccountLimit.objects.filter(id_account__id_user=user).order_by("-start_date")

    def perform_create(self, serializer):
        user = self.get_logged_user_or_raise()
        account = serializer.validated_data.get("id_account")
        if account.id_user_id != user.id_user:
            from rest_framework.exceptions import PermissionDenied

            raise PermissionDenied("La cuenta no pertenece al usuario actual.")
        serializer.save()


class MovementViewSet(LoginRequiredViewSet):
    serializer_class = MovementSerializer

    def get_queryset(self):
        user = self.get_logged_user_or_raise()
        return (
            Movement.objects.select_related(
                "id_account",
                "id_destination_account",
                "id_category",
                "id_service",
                "id_exchange_rate",
            )
            .filter(id_account__id_user=user)
            .order_by("-movement_date", "-id_movement")
        )

    def create(self, request, *args, **kwargs):
        user = self.get_logged_user_or_raise()
        data = request.data
        destination_id = data.get("id_destination_account")

        # Si hay cuenta destino, se trata como transferencia.
        # En transferencias ya NO se solicita categoría al usuario:
        # se usa la categoría principal definida en la cuenta destino.
        is_transfer = bool(destination_id)

        required = ["id_account", "amount", "movement_date", "original_currency"]
        missing = [field for field in required if not data.get(field)]
        if missing:
            return Response(
                {"error": "Faltan campos obligatorios", "fields": missing},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            origin_account = Account.objects.get(
                id_account=data.get("id_account"),
                id_user=user,
            )
        except Account.DoesNotExist:
            return Response(
                {"error": "La cuenta origen no pertenece al usuario actual."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        destination_account = None
        category_id = data.get("id_category")

        if is_transfer:
            try:
                destination_account = Account.objects.get(
                    id_account=destination_id,
                    id_user=user,
                )
            except Account.DoesNotExist:
                return Response(
                    {"error": "La cuenta destino no pertenece al usuario actual."},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            if origin_account.id_account == destination_account.id_account:
                return Response(
                    {"error": "La cuenta origen y destino no pueden ser la misma."},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            category_id = destination_account.id_main_category_id
            if not category_id:
                return Response(
                    {
                        "error": (
                            "La cuenta destino no tiene categoría principal definida. "
                            "Asigna una categoría principal a la cuenta destino antes de transferir."
                        )
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )
        else:
            if not Category.objects.filter(id_category=category_id, id_user=user).exists():
                return Response(
                    {"error": "La categoría no pertenece al usuario actual."},
                    status=status.HTTP_400_BAD_REQUEST,
                )

        if data.get("id_service") and not Service.objects.filter(
            id_service=data.get("id_service"), id_user=user
        ).exists():
            return Response(
                {"error": "El servicio no pertenece al usuario actual."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if is_transfer:
            try:
                amount = Decimal(str(data.get("amount")))
            except Exception:
                return Response(
                    {"error": "Monto inválido"},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            if amount <= 0:
                return Response(
                    {"error": "El monto de la transferencia debe ser mayor que cero."},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            with transaction.atomic():
                last_group = (
                    Movement.objects.filter(id_account__id_user=user)
                    .exclude(transfer_group_id__isnull=True)
                    .order_by("-transfer_group_id")
                    .values_list("transfer_group_id", flat=True)
                    .first()
                    or 0
                )
                group_id = int(last_group) + 1
                common = {
                    "id_category_id": category_id,
                    "id_service_id": data.get("id_service") or None,
                    "id_exchange_rate_id": data.get("id_exchange_rate") or None,
                    "transfer_group_id": group_id,
                    "original_currency": data.get("original_currency"),
                    "movement_date": data.get("movement_date"),
                }
                salida = Movement.objects.create(
                    id_account=origin_account,
                    id_destination_account=destination_account,
                    amount=-abs(amount),
                    description=data.get("description") or "Movimiento enviado",
                    **common,
                )

                # Si la cuenta destino es de tipo GASTO, NO se crea un ingreso positivo.
                # Ejemplo: Efectivo -> Gasolina debe quedar como un gasto, no como gasto + ingreso.
                if destination_account.account_type == "GASTO":
                    return Response(
                        {
                            "message": "Gasto registrado desde cuenta destino de tipo GASTO",
                            "category_used": category_id,
                            "gasto": MovementSerializer(salida).data,
                        },
                        status=status.HTTP_201_CREATED,
                    )

                # Para transferencias reales entre cuentas patrimoniales, sí se crea
                # una salida en la cuenta origen y una entrada en la cuenta destino.
                entrada = Movement.objects.create(
                    id_account=destination_account,
                    id_destination_account=origin_account,
                    amount=abs(amount),
                    description=data.get("description") or "Transferencia recibida",
                    **common,
                )
                return Response(
                    {
                        "message": "Transferencia creada",
                        "category_used": category_id,
                        "salida": MovementSerializer(salida).data,
                        "entrada": MovementSerializer(entrada).data,
                    },
                    status=status.HTTP_201_CREATED,
                )

        return super().create(request, *args, **kwargs)


@api_view(["GET"])
def dashboard(request):
    user, error = require_login(request)
    if error:
        return error

    accounts = Account.objects.filter(id_user=user)
    movements = Movement.objects.filter(id_account__id_user=user)

    income = movements.filter(amount__gt=0).aggregate(total=Sum("amount"))["total"] or 0
    expenses = movements.filter(amount__lt=0).aggregate(total=Sum("amount"))["total"] or 0
    balance = income + expenses

    return Response(
        {
            "current_user": PublicUserSerializer(user).data,
            "total_users": 1,
            "total_accounts": accounts.count(),
            "income": income,
            "expenses": abs(expenses),
            "balance": balance,
        }
    )
