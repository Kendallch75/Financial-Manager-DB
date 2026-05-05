USE flujex;

INSERT INTO USER (
    first_name,
    last_name_1,
    last_name_2,
    email,
    password_hash,
    password_hash_2
) VALUES (
    'Kendal',
    'Demo',
    'Usuario',
    'demo@flujex.local',
    'pbkdf2_sha256$1200000$tNT93Fdf1gNUl81RoFoGE0$dKRixqKYrd+GSCnmPu33pcu9rfc9L1yXB4dMIsGD7Xw=',
    NULL
);

INSERT INTO CATEGORY (id_user, name, type, description, color)
VALUES
    (1, 'Alimentación', 'EXPENSE', 'Comidas, supermercado y restaurantes', '#ef4444'),
    (1, 'Transporte', 'EXPENSE', 'Bus, combustible, Uber o mantenimiento', '#f97316'),
    (1, 'Salario', 'INCOME', 'Ingresos principales', '#22c55e'),
    (1, 'Servicios', 'EXPENSE', 'Pagos de servicios públicos', '#3b82f6');

INSERT INTO ACCOUNT (id_user, account_name, account_type, currency, id_main_category)
VALUES
    (1, 'Efectivo', 'ACTIVO', 'CRC', NULL),
    (1, 'Banco principal', 'ACTIVO', 'CRC', NULL),
    (1, 'Tarjeta de crédito', 'PASIVO', 'CRC', NULL);

INSERT INTO SERVICE (
    id_user,
    service_name,
    provider_name,
    reference_number,
    due_day,
    typical_amount,
    currency
) VALUES (
    1,
    'Electricidad',
    'Proveedor demo',
    'NISE-DEMO-001',
    15,
    25000.00,
    'CRC'
);

INSERT INTO EXCHANGE_RATE (from_currency, to_currency, rate, rate_date)
VALUES
    ('USD', 'CRC', 520.0000, NOW()),
    ('CRC', 'USD', 0.0019, NOW());

INSERT INTO MOVEMENT (
    id_account,
    id_destination_account,
    id_category,
    id_service,
    id_exchange_rate,
    transfer_group_id,
    amount,
    original_currency,
    description,
    movement_date
) VALUES
    (2, NULL, 3, NULL, NULL, NULL, 350000.00, 'CRC', 'Salario demo', CURDATE()),
    (2, NULL, 1, NULL, NULL, NULL, -12500.00, 'CRC', 'Supermercado demo', CURDATE()),
    (2, NULL, 4, 1, NULL, NULL, -25000.00, 'CRC', 'Pago electricidad demo', CURDATE());

INSERT INTO ACCOUNT_LIMIT (id_account, start_date, end_date, max_amount)
VALUES
    (2, DATE_FORMAT(CURDATE(), '%Y-%m-01'), LAST_DAY(CURDATE()), 150000.00);
