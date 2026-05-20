-- Stored Procedures simples para Financial Manager / FLUJEX
-- Base de datos: flujex
-- MySQL 8.0

DROP PROCEDURE IF EXISTS sp_listar_cuentas_usuario;
DROP PROCEDURE IF EXISTS sp_crear_categoria_simple;
DROP PROCEDURE IF EXISTS sp_crear_cuenta_simple;
DROP PROCEDURE IF EXISTS sp_registrar_movimiento_simple;
DROP PROCEDURE IF EXISTS sp_resumen_mensual_usuario;
DROP PROCEDURE IF EXISTS sp_movimientos_por_cuenta;

DELIMITER //

-- 1. Lista las cuentas activas de un usuario.
CREATE PROCEDURE sp_listar_cuentas_usuario (
    IN p_id_user INT
)
BEGIN
    SELECT
        a.id_account,
        a.account_name,
        a.account_type,
        a.currency,
        c.name AS categoria_principal,
        a.creation_date
    FROM `ACCOUNT` a
    LEFT JOIN `CATEGORY` c ON c.id_category = a.id_main_category
    WHERE a.id_user = p_id_user
      AND a.deleted_at > NOW()
    ORDER BY a.account_name;
END //

-- 2. Crea una categoria simple para un usuario.
CREATE PROCEDURE sp_crear_categoria_simple (
    IN p_id_user INT,
    IN p_name VARCHAR(50),
    IN p_type VARCHAR(20),
    IN p_color VARCHAR(7)
)
BEGIN
    DECLARE EXIT HANDLER FOR SQLEXCEPTION
    BEGIN
        ROLLBACK;
        RESIGNAL;
    END;

    IF p_type NOT IN ('INCOME', 'EXPENSE') THEN
        SIGNAL SQLSTATE '45000'
        SET MESSAGE_TEXT = 'ERROR: El tipo de categoria debe ser INCOME o EXPENSE.';
    END IF;

    START TRANSACTION;

    INSERT INTO `CATEGORY` (
        id_user,
        name,
        type,
        color
    ) VALUES (
        p_id_user,
        p_name,
        p_type,
        COALESCE(p_color, '#64748b')
    );

    COMMIT;

    SELECT LAST_INSERT_ID() AS id_category_creada;
END //

-- 3. Crea una cuenta simple con moneda principal.
CREATE PROCEDURE sp_crear_cuenta_simple (
    IN p_id_user INT,
    IN p_account_name VARCHAR(100),
    IN p_account_type VARCHAR(20),
    IN p_currency CHAR(3),
    IN p_id_main_category INT
)
BEGIN
    DECLARE EXIT HANDLER FOR SQLEXCEPTION
    BEGIN
        ROLLBACK;
        RESIGNAL;
    END;

    IF p_account_type NOT IN ('ACTIVO', 'PASIVO', 'CAPITAL', 'INGRESO', 'GASTO') THEN
        SIGNAL SQLSTATE '45000'
        SET MESSAGE_TEXT = 'ERROR: Tipo de cuenta invalido.';
    END IF;

    IF p_currency NOT IN ('CRC', 'USD', 'EUR') THEN
        SIGNAL SQLSTATE '45000'
        SET MESSAGE_TEXT = 'ERROR: Moneda invalida. Use CRC, USD o EUR.';
    END IF;

    START TRANSACTION;

    INSERT INTO `ACCOUNT` (
        id_user,
        account_name,
        account_type,
        currency,
        id_main_category
    ) VALUES (
        p_id_user,
        p_account_name,
        p_account_type,
        p_currency,
        p_id_main_category
    );

    COMMIT;

    SELECT LAST_INSERT_ID() AS id_account_creada;
END //

-- 4. Registra un movimiento simple.
-- La categoria y la moneda se toman automaticamente de la cuenta.
CREATE PROCEDURE sp_registrar_movimiento_simple (
    IN p_id_account INT,
    IN p_amount DECIMAL(10,2),
    IN p_description VARCHAR(255),
    IN p_movement_date DATE
)
BEGIN
    DECLARE v_id_category INT;
    DECLARE v_currency CHAR(3);

    DECLARE EXIT HANDLER FOR SQLEXCEPTION
    BEGIN
        ROLLBACK;
        RESIGNAL;
    END;

    IF p_amount = 0 THEN
        SIGNAL SQLSTATE '45000'
        SET MESSAGE_TEXT = 'ERROR: El monto no puede ser cero.';
    END IF;

    SELECT id_main_category, currency
    INTO v_id_category, v_currency
    FROM `ACCOUNT`
    WHERE id_account = p_id_account
      AND deleted_at > NOW();

    START TRANSACTION;

    INSERT INTO `MOVEMENT` (
        id_account,
        id_category,
        amount,
        original_currency,
        description,
        movement_date
    ) VALUES (
        p_id_account,
        v_id_category,
        p_amount,
        v_currency,
        p_description,
        COALESCE(p_movement_date, CURDATE())
    );

    COMMIT;

    SELECT LAST_INSERT_ID() AS id_movement_creado;
END //

-- 5. Resume ingresos, gastos y balance de un usuario en un mes.
CREATE PROCEDURE sp_resumen_mensual_usuario (
    IN p_id_user INT,
    IN p_anio INT,
    IN p_mes INT
)
BEGIN
    SELECT
        p_anio AS anio,
        p_mes AS mes,
        COALESCE(SUM(CASE WHEN m.amount > 0 THEN m.amount ELSE 0 END), 0) AS total_ingresos,
        COALESCE(SUM(CASE WHEN m.amount < 0 THEN ABS(m.amount) ELSE 0 END), 0) AS total_gastos,
        COALESCE(SUM(m.amount), 0) AS balance
    FROM `MOVEMENT` m
    INNER JOIN `ACCOUNT` a ON a.id_account = m.id_account
    WHERE a.id_user = p_id_user
      AND YEAR(m.movement_date) = p_anio
      AND MONTH(m.movement_date) = p_mes;
END //

-- 6. Lista movimientos de una cuenta en un rango de fechas.
CREATE PROCEDURE sp_movimientos_por_cuenta (
    IN p_id_account INT,
    IN p_fecha_inicio DATE,
    IN p_fecha_fin DATE
)
BEGIN
    IF p_fecha_inicio > p_fecha_fin THEN
        SIGNAL SQLSTATE '45000'
        SET MESSAGE_TEXT = 'ERROR: La fecha de inicio no puede ser mayor a la fecha fin.';
    END IF;

    SELECT
        m.id_movement,
        m.movement_date,
        a.account_name,
        c.name AS categoria,
        m.amount,
        m.original_currency,
        m.description
    FROM `MOVEMENT` m
    INNER JOIN `ACCOUNT` a ON a.id_account = m.id_account
    INNER JOIN `CATEGORY` c ON c.id_category = m.id_category
    WHERE m.id_account = p_id_account
      AND m.movement_date BETWEEN p_fecha_inicio AND p_fecha_fin
    ORDER BY m.movement_date DESC, m.id_movement DESC;
END //

DELIMITER ;

-- Pruebas rapidas:
-- CALL sp_listar_cuentas_usuario(1);
-- CALL sp_crear_categoria_simple(1, 'Comida', 'EXPENSE', '#ef4444');
-- CALL sp_crear_cuenta_simple(1, 'Efectivo', 'ACTIVO', 'CRC', 1);
-- CALL sp_registrar_movimiento_simple(1, -2500.00, 'Compra simple', CURDATE());
-- CALL sp_resumen_mensual_usuario(1, 2026, 5);
-- CALL sp_movimientos_por_cuenta(1, '2026-01-01', '2026-12-31');
