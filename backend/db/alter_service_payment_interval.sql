USE flujex;

ALTER TABLE SERVICE
ADD COLUMN payment_interval_months INT NOT NULL DEFAULT 1 AFTER due_day;

ALTER TABLE SERVICE
ADD CONSTRAINT chk_service_payment_interval
CHECK (payment_interval_months BETWEEN 1 AND 24);
