USE flujex;

-- 1. Obtener movimientos de un usuario.
SELECT
    m.id_movement,
    u.email,
    a.account_name,
    c.name AS category,
    c.type AS category_type,
    m.amount,
    m.original_currency,
    m.description,
    m.movement_date
FROM MOVEMENT m
JOIN ACCOUNT a ON m.id_account = a.id_account
JOIN USER u ON a.id_user = u.id_user
JOIN CATEGORY c ON m.id_category = c.id_category
WHERE u.id_user = ?
ORDER BY m.movement_date DESC;

-- 2. Resumen de gastos por categoría del mes actual.
SELECT
    c.name AS category,
    COUNT(m.id_movement) AS quantity,
    SUM(ABS(m.amount)) AS total,
    AVG(ABS(m.amount)) AS average_amount
FROM MOVEMENT m
JOIN CATEGORY c ON m.id_category = c.id_category
JOIN ACCOUNT a ON m.id_account = a.id_account
WHERE a.id_user = ?
  AND c.type = 'EXPENSE'
  AND MONTH(m.movement_date) = MONTH(CURDATE())
  AND YEAR(m.movement_date) = YEAR(CURDATE())
GROUP BY c.id_category, c.name
ORDER BY total DESC;

-- 3. Resumen de ingresos por categoría.
SELECT
    c.name AS category,
    COUNT(m.id_movement) AS quantity,
    SUM(m.amount) AS total
FROM MOVEMENT m
JOIN CATEGORY c ON m.id_category = c.id_category
JOIN ACCOUNT a ON m.id_account = a.id_account
WHERE a.id_user = ?
  AND c.type = 'INCOME'
GROUP BY c.id_category, c.name
ORDER BY total DESC;

-- 4. Balance calculado por cuenta.
SELECT
    a.id_account,
    a.account_name,
    a.account_type,
    a.currency,
    COALESCE(SUM(m.amount), 0) AS calculated_balance
FROM ACCOUNT a
LEFT JOIN MOVEMENT m ON a.id_account = m.id_account
WHERE a.id_user = ?
  AND a.deleted_at = '2099-12-31 23:59:59'
GROUP BY a.id_account, a.account_name, a.account_type, a.currency
ORDER BY a.creation_date DESC;

-- 5. Servicios próximos a vencer.
SELECT
    s.id_service,
    s.service_name,
    s.provider_name,
    s.reference_number,
    s.due_day,
    s.typical_amount,
    s.currency
FROM SERVICE s
WHERE s.id_user = ?
  AND s.cancellation_date = '2099-12-31 23:59:59'
ORDER BY s.due_day ASC;

-- 6. Movimientos asociados a transferencias.
SELECT
    transfer_group_id,
    COUNT(*) AS movements_in_group,
    SUM(amount) AS net_amount,
    SUM(ABS(amount)) AS gross_amount
FROM MOVEMENT
WHERE transfer_group_id IS NOT NULL
GROUP BY transfer_group_id
ORDER BY transfer_group_id DESC;
