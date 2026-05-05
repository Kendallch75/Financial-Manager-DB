USE flujex;

CREATE INDEX idx_user_email
ON USER(email);

CREATE INDEX idx_category_user
ON CATEGORY(id_user);

CREATE INDEX idx_category_user_type
ON CATEGORY(id_user, type);

CREATE INDEX idx_account_user
ON ACCOUNT(id_user);

CREATE INDEX idx_account_user_deleted
ON ACCOUNT(id_user, deleted_at);

CREATE INDEX idx_service_user
ON SERVICE(id_user);

CREATE INDEX idx_service_due_day
ON SERVICE(id_user, due_day);

CREATE INDEX idx_exchange_rate_pair_date
ON EXCHANGE_RATE(from_currency, to_currency, rate_date);

CREATE INDEX idx_movement_account
ON MOVEMENT(id_account);

CREATE INDEX idx_movement_category
ON MOVEMENT(id_category);

CREATE INDEX idx_movement_date
ON MOVEMENT(movement_date);

CREATE INDEX idx_movement_account_date
ON MOVEMENT(id_account, movement_date);

CREATE INDEX idx_movement_transfer_group
ON MOVEMENT(transfer_group_id);

CREATE INDEX idx_account_limit_account
ON ACCOUNT_LIMIT(id_account);

CREATE INDEX idx_account_limit_dates
ON ACCOUNT_LIMIT(start_date, end_date);
