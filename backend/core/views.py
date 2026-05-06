from decimal import Decimal

from django.conf import settings
from django.contrib.auth.hashers import check_password, make_password
from django.db import connection, transaction
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

    def _account_main_category_or_error(self, account, role):
        category_id = getattr(account, "id_main_category_id", None)
        if not category_id:
            return None, Response(
                {
                    "error": (
                        f"La cuenta {role} no tiene categoría principal definida. "
                        "Asigna una categoría principal antes de registrar movimientos."
                    )
                },
                status=status.HTTP_400_BAD_REQUEST,
            )
        return category_id, None

    def create(self, request, *args, **kwargs):
        user = self.get_logged_user_or_raise()
        data = request.data
        destination_id = data.get("id_destination_account")

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
                {"error": "La cuenta afectada no pertenece al usuario actual."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        destination_account = None
        if destination_id:
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

        if data.get("id_service") and not Service.objects.filter(
            id_service=data.get("id_service"), id_user=user
        ).exists():
            return Response(
                {"error": "El servicio no pertenece al usuario actual."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            amount = Decimal(str(data.get("amount")))
        except Exception:
            return Response(
                {"error": "Monto inválido"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if amount <= 0:
            return Response(
                {"error": "El monto debe ser mayor a cero."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        common_optional = {
            "id_service_id": data.get("id_service") or None,
            "id_exchange_rate_id": data.get("id_exchange_rate") or None,
            "original_currency": data.get("original_currency"),
            "movement_date": data.get("movement_date"),
        }

        # Caso nuevo: registrar un ingreso sin cuenta destino.
        # Ejemplo: Cuenta afectada = Salario (INGRESO), destino = Sin asignar.
        # Se crea un único movimiento positivo usando la categoría principal de esa cuenta.
        if not destination_account and origin_account.account_type == "INGRESO":
            category_id, error = self._account_main_category_or_error(origin_account, "de ingreso")
            if error:
                return error
            movement = Movement.objects.create(
                id_account=origin_account,
                id_destination_account=None,
                id_category_id=category_id,
                amount=abs(amount),
                description=data.get("description") or "Ingreso registrado",
                transfer_group_id=None,
                **common_optional,
            )
            return Response(MovementSerializer(movement).data, status=status.HTTP_201_CREATED)

        # Caso útil equivalente para gastos directos.
        # Ejemplo: Cuenta afectada = Gasolina (GASTO), destino = Sin asignar.
        # Se crea un único movimiento negativo usando la categoría principal de esa cuenta.
        if not destination_account and origin_account.account_type == "GASTO":
            category_id, error = self._account_main_category_or_error(origin_account, "de gasto")
            if error:
                return error
            movement = Movement.objects.create(
                id_account=origin_account,
                id_destination_account=None,
                id_category_id=category_id,
                amount=-abs(amount),
                description=data.get("description") or "Gasto registrado",
                transfer_group_id=None,
                **common_optional,
            )
            return Response(MovementSerializer(movement).data, status=status.HTTP_201_CREATED)

        # Si no hay destino y la cuenta no es INGRESO/GASTO, la transacción es ambigua.
        # Para ACTIVO/PASIVO/CAPITAL se debe escoger una cuenta destino o usar una cuenta tipo INGRESO/GASTO.
        if not destination_account:
            return Response(
                {
                    "error": (
                        "Para registrar un movimiento sin cuenta destino, la cuenta afectada debe ser "
                        "de tipo INGRESO o GASTO. Para mover dinero desde Efectivo/Banco, selecciona una cuenta destino."
                    )
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        with transaction.atomic():
            last_group = (
                Movement.objects.filter(id_account__id_user=user)
                .exclude(transfer_group_id=None)
                .order_by("-transfer_group_id")
                .values_list("transfer_group_id", flat=True)
                .first()
                or 0
            )
            group_id = int(last_group) + 1

            # Ingreso desde cuenta tipo INGRESO hacia una cuenta real.
            # Ejemplo: Salario (INGRESO) → Efectivo (ACTIVO).
            # Se registra solo una entrada positiva en la cuenta destino.
            if origin_account.account_type == "INGRESO":
                category_id, error = self._account_main_category_or_error(origin_account, "de ingreso")
                if error:
                    return error
                movement = Movement.objects.create(
                    id_account=destination_account,
                    id_destination_account=None,
                    id_category_id=category_id,
                    amount=abs(amount),
                    description=data.get("description") or f"Ingreso desde {origin_account.account_name}",
                    transfer_group_id=group_id,
                    **common_optional,
                )
                return Response(MovementSerializer(movement).data, status=status.HTTP_201_CREATED)

            # Gasto desde una cuenta real hacia una cuenta tipo GASTO.
            # Ejemplo: Efectivo (ACTIVO) → Gasolina (GASTO).
            # Se registra solo una salida negativa desde la cuenta origen.
            if destination_account.account_type == "GASTO":
                category_id, error = self._account_main_category_or_error(destination_account, "de gasto destino")
                if error:
                    return error
                movement = Movement.objects.create(
                    id_account=origin_account,
                    id_destination_account=destination_account,
                    id_category_id=category_id,
                    amount=-abs(amount),
                    description=data.get("description") or f"Gasto en {destination_account.account_name}",
                    transfer_group_id=group_id,
                    **common_optional,
                )
                return Response(MovementSerializer(movement).data, status=status.HTTP_201_CREATED)

            # Transferencia real entre cuentas que acumulan saldo.
            # Ejemplo: Efectivo (ACTIVO) → Banco (ACTIVO).
            category_id, error = self._account_main_category_or_error(destination_account, "destino")
            if error:
                return error

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
                description=data.get("description") or "Transferencia enviada",
                **common,
            )
            entrada = Movement.objects.create(
                id_account=destination_account,
                id_destination_account=origin_account,
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




@api_view(["GET"])
def category_spending_report(request):
    user, error = require_login(request)
    if error:
        return error

    start_date = request.GET.get("start_date")
    end_date = request.GET.get("end_date")

    params = [user.id_user]
    date_filter = ""

    if start_date:
        date_filter += " AND m.movement_date >= %s"
        params.append(start_date)

    if end_date:
        date_filter += " AND m.movement_date <= %s"
        params.append(end_date)

    query = f"""
        SELECT
            c.name AS category,
            SUM(ABS(m.amount)) AS total
        FROM MOVEMENT m
        JOIN ACCOUNT a ON m.id_account = a.id_account
        JOIN CATEGORY c ON m.id_category = c.id_category
        WHERE a.id_user = %s
          AND c.type = 'EXPENSE'
          AND m.amount < 0
          {date_filter}
        GROUP BY c.id_category, c.name
        ORDER BY total DESC
    """

    with connection.cursor() as cursor:
        cursor.execute(query, params)
        rows = cursor.fetchall()

    total_spent = sum(float(row[1] or 0) for row in rows)
    items = []

    for category, total in rows:
        value = float(total or 0)
        percentage = (value / total_spent * 100) if total_spent else 0
        items.append(
            {
                "category": category,
                "total": value,
                "percentage": percentage,
            }
        )

    return Response(
        {
            "total": total_spent,
            "items": items,
        }
    )

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
