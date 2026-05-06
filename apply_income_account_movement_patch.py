from pathlib import Path
import re

ROOT = Path.cwd()
views_path = ROOT / 'backend' / 'core' / 'views.py'
if not views_path.exists():
    raise SystemExit('No encontré backend/core/views.py. Ejecuta este script desde la raíz del proyecto.')

text = views_path.read_text(encoding='utf-8')

new_class = r'''class MovementViewSet(LoginRequiredViewSet):
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
'''

pattern = r'class MovementViewSet\(LoginRequiredViewSet\):.*?\n\n@api_view\(\["GET"\]\)\ndef dashboard'
match = re.search(pattern, text, flags=re.S)
if not match:
    raise SystemExit('No pude encontrar la clase MovementViewSet completa para reemplazarla.')

replacement = new_class + '\n\n@api_view(["GET"])\ndef dashboard'
new_text = re.sub(pattern, replacement, text, count=1, flags=re.S)

backup = views_path.with_suffix('.py.bak_income_account_patch')
backup.write_text(text, encoding='utf-8')
views_path.write_text(new_text, encoding='utf-8')

print('Parche aplicado correctamente en backend/core/views.py')
print(f'Copia de seguridad: {backup}')
