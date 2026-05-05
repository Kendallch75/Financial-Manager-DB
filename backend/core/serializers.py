from django.conf import settings
from django.contrib.auth.hashers import make_password
from rest_framework import serializers

from .models import (
    Account,
    AccountLimit,
    Category,
    ExchangeRate,
    Movement,
    Service,
    User,
)


class UserSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=False)
    password_hash = serializers.CharField(read_only=True)
    password_hash_2 = serializers.CharField(read_only=True)
    cancellation_date = serializers.DateTimeField(read_only=True)

    class Meta:
        model = User
        fields = [
            "id_user",
            "first_name",
            "last_name_1",
            "last_name_2",
            "email",
            "password",
            "password_hash",
            "password_hash_2",
            "registration_date",
            "cancellation_date",
        ]

    def create(self, validated_data):
        password = validated_data.pop("password", None)

        if not password:
            raise serializers.ValidationError({"password": "La contraseña es obligatoria."})

        validated_data["password_hash"] = make_password(password)
        validated_data["password_hash_2"] = make_password(password + settings.SECRET_KEY)

        return User.objects.create(**validated_data)

    def update(self, instance, validated_data):
        password = validated_data.pop("password", None)

        for attr, value in validated_data.items():
            setattr(instance, attr, value)

        if password:
            instance.password_hash = make_password(password)
            instance.password_hash_2 = make_password(password + settings.SECRET_KEY)

        instance.save()
        return instance


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = "__all__"


class AccountSerializer(serializers.ModelSerializer):
    deleted_at = serializers.DateTimeField(read_only=True)

    class Meta:
        model = Account
        fields = "__all__"


class ServiceSerializer(serializers.ModelSerializer):
    cancellation_date = serializers.DateTimeField(read_only=True)

    class Meta:
        model = Service
        fields = "__all__"


class ExchangeRateSerializer(serializers.ModelSerializer):
    class Meta:
        model = ExchangeRate
        fields = "__all__"


class MovementSerializer(serializers.ModelSerializer):
    class Meta:
        model = Movement
        fields = "__all__"


class AccountLimitSerializer(serializers.ModelSerializer):
    class Meta:
        model = AccountLimit
        fields = "__all__"
