USE flujex;

SET FOREIGN_KEY_CHECKS = 0;

DROP TABLE IF EXISTS ACCOUNT_LIMIT;
DROP TABLE IF EXISTS MOVEMENT;
DROP TABLE IF EXISTS EXCHANGE_RATE;
DROP TABLE IF EXISTS SERVICE;
DROP TABLE IF EXISTS ACCOUNT;
DROP TABLE IF EXISTS CATEGORY;
DROP TABLE IF EXISTS USER;

SET FOREIGN_KEY_CHECKS = 1;

CREATE TABLE USER (
    id_user INT AUTO_INCREMENT PRIMARY KEY,
    first_name VARCHAR(100) NOT NULL,
    last_name_1 VARCHAR(100) NOT NULL,
    last_name_2 VARCHAR(100),
    email VARCHAR(100) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    password_hash_2 VARCHAR(255),
    registration_date DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    cancellation_date DATETIME NOT NULL DEFAULT '2099-12-31 23:59:59'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE CATEGORY (
    id_category INT AUTO_INCREMENT PRIMARY KEY,
    id_user INT NOT NULL,
    name VARCHAR(50) NOT NULL,
    type ENUM('EXPENSE', 'INCOME') NOT NULL,
    description VARCHAR(255),
    color VARCHAR(7),
    creation_date DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT fk_category_user
        FOREIGN KEY (id_user)
        REFERENCES USER(id_user)
        ON DELETE CASCADE,

    CONSTRAINT uq_category_user_name_type
        UNIQUE (id_user, name, type)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE ACCOUNT (
    id_account INT AUTO_INCREMENT PRIMARY KEY,
    id_user INT NOT NULL,
    account_name VARCHAR(100) NOT NULL,
    account_type ENUM('ACTIVO', 'PASIVO', 'CAPITAL', 'INGRESO', 'GASTO') NOT NULL,
    currency CHAR(3) NOT NULL,
    id_main_category INT,
    creation_date DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    deleted_at DATETIME NOT NULL DEFAULT '2099-12-31 23:59:59',

    CONSTRAINT fk_account_user
        FOREIGN KEY (id_user)
        REFERENCES USER(id_user)
        ON DELETE CASCADE,

    CONSTRAINT fk_account_main_category
        FOREIGN KEY (id_main_category)
        REFERENCES CATEGORY(id_category)
        ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE SERVICE (
    id_service INT AUTO_INCREMENT PRIMARY KEY,
    id_user INT NOT NULL,
    service_name VARCHAR(100) NOT NULL,
    provider_name VARCHAR(100),
    reference_number VARCHAR(100),
    due_day INT NOT NULL,
    typical_amount DECIMAL(10, 2),
    currency CHAR(3) NOT NULL,
    cancellation_date DATETIME NOT NULL DEFAULT '2099-12-31 23:59:59',
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT fk_service_user
        FOREIGN KEY (id_user)
        REFERENCES USER(id_user)
        ON DELETE CASCADE,

    CONSTRAINT chk_service_due_day
        CHECK (due_day BETWEEN 1 AND 31)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE EXCHANGE_RATE (
    id_exchange_rate INT AUTO_INCREMENT PRIMARY KEY,
    from_currency CHAR(3) NOT NULL,
    to_currency CHAR(3) NOT NULL,
    rate DECIMAL(10, 4) NOT NULL,
    rate_date DATETIME NOT NULL,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT chk_exchange_rate_positive
        CHECK (rate > 0)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE MOVEMENT (
    id_movement INT AUTO_INCREMENT PRIMARY KEY,
    id_account INT NOT NULL,
    id_destination_account INT,
    id_category INT NOT NULL,
    id_service INT,
    id_exchange_rate INT,
    transfer_group_id INT,
    amount DECIMAL(10, 2) NOT NULL,
    original_currency CHAR(3) NOT NULL,
    description VARCHAR(255),
    movement_date DATE NOT NULL,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT fk_movement_account
        FOREIGN KEY (id_account)
        REFERENCES ACCOUNT(id_account)
        ON DELETE CASCADE,

    CONSTRAINT fk_movement_destination_account
        FOREIGN KEY (id_destination_account)
        REFERENCES ACCOUNT(id_account)
        ON DELETE SET NULL,

    CONSTRAINT fk_movement_category
        FOREIGN KEY (id_category)
        REFERENCES CATEGORY(id_category)
        ON DELETE CASCADE,

    CONSTRAINT fk_movement_service
        FOREIGN KEY (id_service)
        REFERENCES SERVICE(id_service)
        ON DELETE SET NULL,

    CONSTRAINT fk_movement_exchange_rate
        FOREIGN KEY (id_exchange_rate)
        REFERENCES EXCHANGE_RATE(id_exchange_rate)
        ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE ACCOUNT_LIMIT (
    id_limit INT AUTO_INCREMENT PRIMARY KEY,
    id_account INT NOT NULL,
    start_date DATE NOT NULL,
    end_date DATE NOT NULL,
    max_amount DECIMAL(10, 2) NOT NULL,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT fk_account_limit_account
        FOREIGN KEY (id_account)
        REFERENCES ACCOUNT(id_account)
        ON DELETE CASCADE,

    CONSTRAINT chk_account_limit_dates
        CHECK (end_date >= start_date),

    CONSTRAINT chk_account_limit_amount
        CHECK (max_amount > 0)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
