from pathlib import Path

ROOT = Path.cwd()
views_path = ROOT / "backend" / "core" / "views.py"
main_path = ROOT / "frontend" / "src" / "main.jsx"

if not views_path.exists():
    raise SystemExit(f"No se encontro {views_path}. Ejecuta este script desde la raiz del proyecto.")
if not main_path.exists():
    raise SystemExit(f"No se encontro {main_path}. Ejecuta este script desde la raiz del proyecto.")

views = views_path.read_text(encoding="utf-8")

# Imports necesarios para promedio absoluto de pagos por servicio.
views = views.replace("from django.db.models import Sum", "from django.db.models import Sum, Avg")
if "from django.db.models.functions import Abs" not in views:
    views = views.replace(
        "from django.db.models import Sum, Avg",
        "from django.db.models import Sum, Avg\nfrom django.db.models.functions import Abs",
    )

old_service_class = '''class ServiceViewSet(LoginRequiredViewSet):
    serializer_class = ServiceSerializer

    def get_queryset(self):
        user = self.get_logged_user_or_raise()
        return Service.objects.filter(id_user=user).order_by("due_day", "service_name")

    def perform_create(self, serializer):
        serializer.save(id_user=self.get_logged_user_or_raise())'''

new_service_class = '''class ServiceViewSet(LoginRequiredViewSet):
    serializer_class = ServiceSerializer

    def get_queryset(self):
        user = self.get_logged_user_or_raise()
        return Service.objects.filter(id_user=user).order_by("due_day", "service_name")

    def _average_paid_for_service(self, service, user):
        """
        Calcula el promedio histórico pagado en un servicio.
        Usa los movimientos asociados a ese servicio y toma el valor absoluto
        para que gastos negativos se muestren como monto positivo.
        """
        avg = (
            Movement.objects.filter(
                id_service=service,
                id_account__id_user=user,
            )
            .exclude(amount=0)
            .aggregate(avg=Avg(Abs("amount")))
            .get("avg")
        )
        if avg is None:
            return Decimal("0.00")
        return Decimal(avg).quantize(Decimal("0.01"))

    def _serialize_with_average(self, service, user):
        data = ServiceSerializer(service).data
        average = self._average_paid_for_service(service, user)
        # Se mantiene el nombre typical_amount para no romper el frontend,
        # pero ahora representa un valor calculado por request.
        data["typical_amount"] = str(average)
        data["average_paid"] = str(average)
        return data

    def list(self, request, *args, **kwargs):
        user = self.get_logged_user_or_raise()
        services = self.get_queryset()
        return Response([self._serialize_with_average(service, user) for service in services])

    def retrieve(self, request, *args, **kwargs):
        user = self.get_logged_user_or_raise()
        service = self.get_object()
        return Response(self._serialize_with_average(service, user))

    def perform_create(self, serializer):
        # typical_amount ya no se digita: se calcula desde MOVEMENT.
        serializer.save(id_user=self.get_logged_user_or_raise(), typical_amount=None)

    def perform_update(self, serializer):
        # Evita que typical_amount sea editado manualmente si llega en el payload.
        serializer.save(typical_amount=None)'''

if old_service_class not in views:
    raise SystemExit("No pude encontrar exactamente la clase ServiceViewSet esperada. Revisa si views.py cambió mucho.")
views = views.replace(old_service_class, new_service_class)
views_path.write_text(views, encoding="utf-8")

main = main_path.read_text(encoding="utf-8")

# Quitar typical_amount del formulario de servicios, pero dejarlo visible en tabla/response.
main = main.replace(
    "fields: [ 'service_name', 'provider_name', 'reference_number', 'due_day', 'typical_amount', 'currency', ],",
    "fields: [ 'service_name', 'provider_name', 'reference_number', 'due_day', 'currency' ],",
)
main = main.replace("typical_amount: 'Monto típico'", "typical_amount: 'Promedio pagado'")

# Insertar configuración para columnas extra de solo lectura en servicios.
if "const extraDisplayFields" not in main:
    marker = "const relationConfig = {"
    insert = """const extraDisplayFields = {
  services: ['typical_amount'],
};

"""
    if marker not in main:
        raise SystemExit("No pude ubicar relationConfig en main.jsx.")
    main = main.replace(marker, insert + marker)

# Cambiar visibleFields para incluir campos extra de visualización.
main = main.replace(
    "const visibleFields = config.fields;",
    "const visibleFields = [\n    ...config.fields,\n    ...(extraDisplayFields[Object.keys(resources).find((key) => resources[key] === config)] || []),\n  ];",
)

# Evitar editar campos de solo lectura si aparecen en visibleFields.
main = main.replace(
    "{visibleFields.map((field) => (  {fieldLabels[field] || field} {renderField(field)}  ))}",
    "{config.fields.map((field) => (  {fieldLabels[field] || field} {renderField(field)}  ))}",
)

# Si hay render de tabla usando config.fields, cambiarlo a visibleFields para mostrar promedio.
main = main.replace("{config.fields.slice(0, 5).map((field) => ( ))}", "{visibleFields.slice(0, 5).map((field) => ( ))}")
main = main.replace("{config.fields.slice(0, 5).map((field) => ( ))}", "{visibleFields.slice(0, 5).map((field) => ( ))}")

# Los headers/celdas en el raw comprimido pueden estar en una misma expresión; refuerzo simple.
main = main.replace("{config.fields.slice(0, 5).map((field) => ( ))}", "{visibleFields.slice(0, 5).map((field) => ( ))}")

main_path.write_text(main, encoding="utf-8")

print("Parche aplicado: Servicios ya no piden monto típico y typical_amount ahora se calcula como promedio pagado por request.")
