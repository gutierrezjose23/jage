-- MySQL 8.0.16+; db-upgrade checks every DDL step before executing it.
-- Existing passenger/admin users and reservations remain intact.
ALTER TABLE users DROP CHECK chk_users_role;
ALTER TABLE users ADD CONSTRAINT chk_users_role CHECK (role IN ('passenger', 'admin', 'driver'));

ALTER TABLE reservations ADD COLUMN driver_id INT NULL;
ALTER TABLE reservations ADD COLUMN commission DECIMAL(12,2) NULL;
ALTER TABLE reservations ADD COLUMN commission_charged BOOLEAN NOT NULL DEFAULT FALSE;
ALTER TABLE reservations ADD COLUMN updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP;
ALTER TABLE reservations ADD INDEX ix_reservations_driver_id (driver_id);
ALTER TABLE reservations ADD CONSTRAINT fk_reservations_driver FOREIGN KEY (driver_id) REFERENCES users(id) ON DELETE RESTRICT;
ALTER TABLE reservations ADD CONSTRAINT chk_reservations_commission CHECK (commission IS NULL OR commission >= 0);

CREATE TABLE driver_wallets (
    driver_id INT NOT NULL,
    balance DECIMAL(12,2) NOT NULL DEFAULT 0.00,
    PRIMARY KEY (driver_id),
    CONSTRAINT fk_wallet_driver FOREIGN KEY (driver_id) REFERENCES users(id) ON DELETE RESTRICT,
    CONSTRAINT chk_wallet_balance CHECK (balance >= 0)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

CREATE TABLE promotions (
    id INT NOT NULL AUTO_INCREMENT,
    title VARCHAR(120) NOT NULL,
    description VARCHAR(500) NOT NULL DEFAULT '',
    amount DECIMAL(12,2) NOT NULL,
    expires_at DATE NOT NULL,
    active BOOLEAN NOT NULL DEFAULT TRUE,
    created_by INT NOT NULL,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (id),
    CONSTRAINT fk_promotion_admin FOREIGN KEY (created_by) REFERENCES users(id) ON DELETE RESTRICT,
    CONSTRAINT chk_promotion_amount CHECK (amount > 0)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

CREATE TABLE wallet_transactions (
    id INT NOT NULL AUTO_INCREMENT,
    driver_id INT NOT NULL,
    amount DECIMAL(12,2) NOT NULL,
    balance_after DECIMAL(12,2) NOT NULL,
    kind VARCHAR(20) NOT NULL,
    reason VARCHAR(300) NOT NULL,
    reservation_id INT NULL,
    promotion_id INT NULL,
    actor_id INT NULL,
    idempotency_key VARCHAR(36) NULL,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (id),
    KEY ix_wallet_transactions_driver_id (driver_id),
    UNIQUE KEY uq_wallet_reservation (reservation_id),
    UNIQUE KEY uq_wallet_idempotency (idempotency_key),
    UNIQUE KEY uq_driver_promotion (driver_id, promotion_id),
    CONSTRAINT fk_transaction_wallet FOREIGN KEY (driver_id) REFERENCES driver_wallets(driver_id) ON DELETE RESTRICT,
    CONSTRAINT fk_transaction_reservation FOREIGN KEY (reservation_id) REFERENCES reservations(id) ON DELETE RESTRICT,
    CONSTRAINT fk_transaction_promotion FOREIGN KEY (promotion_id) REFERENCES promotions(id) ON DELETE RESTRICT,
    CONSTRAINT fk_transaction_actor FOREIGN KEY (actor_id) REFERENCES users(id) ON DELETE RESTRICT,
    CONSTRAINT chk_transaction_balance CHECK (balance_after >= 0),
    CONSTRAINT chk_transaction_kind CHECK (kind IN ('adjustment', 'commission', 'promotion'))
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

CREATE TABLE rate_limit_buckets (
    key_hash VARCHAR(64) NOT NULL,
    hits INT NOT NULL DEFAULT 0,
    window_start DATETIME NOT NULL,
    PRIMARY KEY (key_hash)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
