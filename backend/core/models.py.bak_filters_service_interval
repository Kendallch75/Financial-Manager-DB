from datetime import datetime

from django.db import models
from django.utils import timezone


def future_date():
    return timezone.make_aware(datetime(2099, 12, 31, 23, 59, 59))


class User(models.Model):
    id_user = models.AutoField(primary_key=True)
    first_name = models.CharField(max_length=100)
    last_name_1 = models.CharField(max_length=100)
    last_name_2 = models.CharField(max_length=100, blank=True, null=True)
    email = models.EmailField(max_length=100, unique=True)
    password_hash = models.CharField(max_length=255)
    password_hash_2 = models.CharField(max_length=255, blank=True, null=True)
    registration_date = models.DateTimeField(auto_now_add=True)
    cancellation_date = models.DateTimeField(default=future_date)

    class Meta:
        db_table = "USER"

    def __str__(self):
        return self.email


class Category(models.Model):
    CATEGORY_TYPES = [
        ("EXPENSE", "Expense"),
        ("INCOME", "Income"),
    ]

    id_category = models.AutoField(primary_key=True)
    id_user = models.ForeignKey(User, on_delete=models.CASCADE, db_column="id_user")
    name = models.CharField(max_length=50)
    type = models.CharField(max_length=10, choices=CATEGORY_TYPES)
    description = models.CharField(max_length=255, blank=True, null=True)
    color = models.CharField(max_length=7, blank=True, null=True)
    creation_date = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "CATEGORY"
        constraints = [
            models.UniqueConstraint(
                fields=["id_user", "name", "type"],
                name="uq_category_user_name_type",
            )
        ]

    def __str__(self):
        return self.name


class Account(models.Model):
    ACCOUNT_TYPES = [
        ("ACTIVO", "Activo"),
        ("PASIVO", "Pasivo"),
        ("CAPITAL", "Capital"),
        ("INGRESO", "Ingreso"),
        ("GASTO", "Gasto"),
    ]

    id_account = models.AutoField(primary_key=True)
    id_user = models.ForeignKey(User, on_delete=models.CASCADE, db_column="id_user")
    account_name = models.CharField(max_length=100)
    account_type = models.CharField(max_length=10, choices=ACCOUNT_TYPES)
    currency = models.CharField(max_length=3)
    id_main_category = models.ForeignKey(
        Category,
        on_delete=models.SET_NULL,
        db_column="id_main_category",
        blank=True,
        null=True,
    )
    creation_date = models.DateTimeField(auto_now_add=True)
    deleted_at = models.DateTimeField(default=future_date)

    class Meta:
        db_table = "ACCOUNT"

    def __str__(self):
        return self.account_name


class Service(models.Model):
    id_service = models.AutoField(primary_key=True)
    id_user = models.ForeignKey(User, on_delete=models.CASCADE, db_column="id_user")
    service_name = models.CharField(max_length=100)
    provider_name = models.CharField(max_length=100, blank=True, null=True)
    reference_number = models.CharField(max_length=100, blank=True, null=True)
    due_day = models.IntegerField()
    typical_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        blank=True,
        null=True,
    )
    currency = models.CharField(max_length=3)
    cancellation_date = models.DateTimeField(default=future_date)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "SERVICE"

    def __str__(self):
        return self.service_name


class ExchangeRate(models.Model):
    id_exchange_rate = models.AutoField(primary_key=True)
    from_currency = models.CharField(max_length=3)
    to_currency = models.CharField(max_length=3)
    rate = models.DecimalField(max_digits=10, decimal_places=4)
    rate_date = models.DateTimeField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "EXCHANGE_RATE"

    def __str__(self):
        return f"{self.from_currency} -> {self.to_currency}: {self.rate}"


class Movement(models.Model):
    id_movement = models.AutoField(primary_key=True)
    id_account = models.ForeignKey(
        Account,
        on_delete=models.CASCADE,
        db_column="id_account",
        related_name="movements",
    )
    id_destination_account = models.ForeignKey(
        Account,
        on_delete=models.SET_NULL,
        db_column="id_destination_account",
        blank=True,
        null=True,
        related_name="destination_movements",
    )
    id_category = models.ForeignKey(Category, on_delete=models.CASCADE, db_column="id_category")
    id_service = models.ForeignKey(
        Service,
        on_delete=models.SET_NULL,
        db_column="id_service",
        blank=True,
        null=True,
    )
    id_exchange_rate = models.ForeignKey(
        ExchangeRate,
        on_delete=models.SET_NULL,
        db_column="id_exchange_rate",
        blank=True,
        null=True,
    )
    transfer_group_id = models.IntegerField(blank=True, null=True)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    original_currency = models.CharField(max_length=3)
    description = models.CharField(max_length=255, blank=True, null=True)
    movement_date = models.DateField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "MOVEMENT"
        indexes = [
            models.Index(fields=["id_account"]),
            models.Index(fields=["id_category"]),
            models.Index(fields=["movement_date"]),
            models.Index(fields=["transfer_group_id"]),
        ]

    def __str__(self):
        return f"{self.amount} - {self.id_account}"


class AccountLimit(models.Model):
    id_limit = models.AutoField(primary_key=True)
    id_account = models.ForeignKey(Account, on_delete=models.CASCADE, db_column="id_account")
    start_date = models.DateField()
    end_date = models.DateField()
    max_amount = models.DecimalField(max_digits=10, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "ACCOUNT_LIMIT"

    def __str__(self):
        return f"{self.id_account} - {self.max_amount}"
