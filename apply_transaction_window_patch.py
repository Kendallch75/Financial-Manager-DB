from pathlib import Path
import re

ROOT = Path.cwd()
main_path = ROOT / 'frontend' / 'src' / 'main.jsx'
views_path = ROOT / 'backend' / 'core' / 'views.py'

if not main_path.exists() or not views_path.exists():
    raise SystemExit('Ejecuta este script desde la raíz del proyecto, donde existen backend/ y frontend/.')

main = main_path.read_text(encoding='utf-8')
views = views_path.read_text(encoding='utf-8')

# 1) Quitar categoría del formulario de movimientos.
# Deja que el backend asigne id_category automáticamente según la cuenta.
main = re.sub(
    r"(movements:\s*\{[^{}]*?fields:\s*\[[^\]]*?)\s*['\"]id_category['\"]\s*,",
    r"\1",
    main,
    flags=re.DOTALL,
)

# Si el archivo está minificado en una sola línea, también intentar reemplazo simple.
main = main.replace("'id_category', 'id_service'", "'id_service'")
main = main.replace('"id_category", "id_service"', '"id_service"')

# 2) Fecha de movimiento por defecto: hoy.
# Reemplaza la función emptyForm para que movement_date nazca con la fecha actual.
empty_form_pattern = r"function\s+emptyForm\s*\(fields\)\s*\{.*?\n\}"
new_empty_form = """function todayISODate() {
  return new Date().toISOString().slice(0, 10);
}

function emptyForm(fields) {
  return Object.fromEntries(
    fields.map((field) => {
      if (field === 'color') return [field, '#22c55e'];
      if (field === 'movement_date') return [field, todayISODate()];
      return [field, ''];
    })
  );
}"""
if re.search(empty_form_pattern, main, flags=re.DOTALL):
    main = re.sub(empty_form_pattern, new_empty_form, main, count=1, flags=re.DOTALL)
else:
    # Si está minificado, reemplazo más laxo.
    main = re.sub(
        r"function emptyForm\(fields\)\{return Object\.fromEntries\(fields\.map\(\(field\)=>\[field,field==='color'\?'#22c55e':''\]\)\)\}",
        new_empty_form,
        main,
        count=1,
    )

# 3) Teclado numérico más cómodo en celular para montos/números.
# Agrega inputMode/pattern/step al input genérico si no existe.
if 'inputMode=' not in main:
    main = main.replace(
        "value={form[field] || ''}",
        "value={form[field] || ''}\n      inputMode={inputType === 'number' ? 'decimal' : undefined}\n      pattern={inputType === 'number' ? '[0-9]*' : undefined}\n      step={inputType === 'number' ? '0.01' : undefined}",
    )
# Reemplazo alterno para archivo minificado de una línea.
if 'inputMode=' not in main:
    main = main.replace(
        "value={form[field]||''}",
        "value={form[field]||''} inputMode={inputType==='number'?'decimal':undefined} pattern={inputType==='number'?'[0-9]*':undefined} step={inputType==='number'?'0.01':undefined}",
    )

# 4) Mejorar etiqueta de cuenta origen si existe.
main = main.replace("id_account: 'Cuenta origen'", "id_account: 'Cuenta afectada'")
main = main.replace('id_account:"Cuenta origen"', 'id_account:"Cuenta afectada"')

# 5) Reemplazar MovementViewSet completo para asignar categoría automáticamente.
new_movement_class = r'''class MovementViewSet(LoginRequiredViewSet):
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

    def _get_user_account(self, account_id, user, label):
        try:
            return Account.objects.get(id_account=account_id, id_user=user)
        except Account.DoesNotExist:
            raise ValueError(f"La cuenta {label} no pertenece al usuario actual.")

    def _category_from_account(self, account, label):
        category_id = getattr(account, "id_main_category_id", None)
        if not category_id:
            raise ValueError(
                f"La cuenta {label} no tiene categoría principal definida. "
                "Asigna una categoría principal antes de registrar movimientos."
            )
        return category_id

    def create(self, request, *args, **kwargs):
        user = self.get_logged_user_or_raise()
        data = request.data.copy()
        destination_id = data.get("id_destination_account")

        required = ["id_account", "amount", "movement_date", "original_currency"]
        missing = [field for field in required if not data.get(field)]
        if missing:
            return Response(
                {"error": "Faltan campos obligatorios", "fields": missing},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            amount = Decimal(str(data.get("amount")))
        except Exception:
            return Response({"error": "Monto inválido"}, status=status.HTTP_400_BAD_REQUEST)

        if amount <= 0:
            return Response(
                {"error": "El monto debe ser mayor que cero."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            origin = self._get_user_account(data.get("id_account"), user, "afectada/origen")
            destination = None
            if destination_id:
                destination = self._get_user_account(destination_id, user, "destino")
        except ValueError as exc:
            return Response({"error": str(exc)}, status=status.HTTP_400_BAD_REQUEST)

        if data.get("id_service") and not Service.objects.filter(
            id_service=data.get("id_service"), id_user=user
        ).exists():
            return Response(
                {"error": "El servicio no pertenece al usuario actual."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            # Caso 1: no hay cuenta destino. El movimiento se clasifica con la
            # categoría principal de la cuenta afectada.
            if not destination:
                category_id = self._category_from_account(origin, "afectada")
                sign = -1 if origin.account_type == "GASTO" else 1
                movement = Movement.objects.create(
                    id_account=origin,
                    id_destination_account=None,
                    id_category_id=category_id,
                    id_service_id=data.get("id_service") or None,
                    id_exchange_rate_id=data.get("id_exchange_rate") or None,
                    amount=amount * sign,
                    original_currency=data.get("original_currency"),
                    description=data.get("description") or "Movimiento registrado",
                    movement_date=data.get("movement_date"),
                )
                return Response(MovementSerializer(movement).data, status=status.HTTP_201_CREATED)

            # Caso 2: destino tipo GASTO. Ejemplo: Efectivo -> Gasolina.
            # Solo se registra una salida/gasto desde la cuenta origen.
            if destination.account_type == "GASTO":
                category_id = self._category_from_account(destination, "destino")
                movement = Movement.objects.create(
                    id_account=origin,
                    id_destination_account=destination,
                    id_category_id=category_id,
                    id_service_id=data.get("id_service") or None,
                    id_exchange_rate_id=data.get("id_exchange_rate") or None,
                    amount=-abs(amount),
                    original_currency=data.get("original_currency"),
                    description=data.get("description") or f"Gasto hacia {destination.account_name}",
                    movement_date=data.get("movement_date"),
                )
                return Response(MovementSerializer(movement).data, status=status.HTTP_201_CREATED)

            # Caso 3: origen tipo INGRESO. Ejemplo: Salario -> Efectivo.
            # Solo se registra una entrada positiva en la cuenta destino.
            if origin.account_type == "INGRESO":
                category_id = self._category_from_account(origin, "origen")
                movement = Movement.objects.create(
                    id_account=destination,
                    id_destination_account=None,
                    id_category_id=category_id,
                    id_service_id=data.get("id_service") or None,
                    id_exchange_rate_id=data.get("id_exchange_rate") or None,
                    amount=abs(amount),
                    original_currency=data.get("original_currency"),
                    description=data.get("description") or f"Ingreso desde {origin.account_name}",
                    movement_date=data.get("movement_date"),
                )
                return Response(MovementSerializer(movement).data, status=status.HTTP_201_CREATED)

            # Caso 4: transferencia real entre cuentas no contables.
            # Ejemplo: Efectivo -> Banco. Se registra salida y entrada.
            category_id = self._category_from_account(destination, "destino")
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
                common = {
                    "id_category_id": category_id,
                    "id_service_id": data.get("id_service") or None,
                    "id_exchange_rate_id": data.get("id_exchange_rate") or None,
                    "transfer_group_id": group_id,
                    "original_currency": data.get("original_currency"),
                    "movement_date": data.get("movement_date"),
                }
                salida = Movement.objects.create(
                    id_account=origin,
                    id_destination_account=destination,
                    amount=-abs(amount),
                    description=data.get("description") or "Transferencia enviada",
                    **common,
                )
                entrada = Movement.objects.create(
                    id_account=destination,
                    id_destination_account=origin,
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
        except ValueError as exc:
            return Response({"error": str(exc)}, status=status.HTTP_400_BAD_REQUEST)
'''

pattern = r"class\s+MovementViewSet\(LoginRequiredViewSet\):.*?\n\n@api_view\(\[\"GET\"\]\)\ndef\s+dashboard"
if re.search(pattern, views, flags=re.DOTALL):
    views = re.sub(pattern, new_movement_class + '\n\n@api_view(["GET"])\ndef dashboard', views, count=1, flags=re.DOTALL)
else:
    raise SystemExit('No pude encontrar class MovementViewSet en backend/core/views.py. No se aplicaron cambios al backend.')

main_path.write_text(main, encoding='utf-8')
views_path.write_text(views, encoding='utf-8')

print('Parche aplicado:')
print('- Fecha de movimientos por defecto = hoy')
print('- Monto con teclado numérico/decimal en móvil')
print('- Categoría eliminada del formulario de movimientos')
print('- Backend asigna categoría según cuenta principal')
