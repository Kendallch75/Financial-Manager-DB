DROP DATABASE IF EXISTS flujex;

CREATE DATABASE flujex
CHARACTER SET utf8mb4
COLLATE utf8mb4_unicode_ci;

CREATE USER IF NOT EXISTS 'flujex_user'@'localhost'
IDENTIFIED BY 'Flujex_User_2026!';

GRANT ALL PRIVILEGES ON flujex.* TO 'flujex_user'@'localhost';

FLUSH PRIVILEGES;
