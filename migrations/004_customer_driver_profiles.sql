-- MySQL 8.0.16+. Shared account/contact data remains in users.
-- NULL preserves existing accounts whose DNI/plate have not been collected.
CREATE TABLE clientes (
    user_id INT NOT NULL,
    dni VARCHAR(8) NULL,
    PRIMARY KEY (user_id),
    CONSTRAINT uq_clientes_dni UNIQUE (dni),
    CONSTRAINT fk_clientes_user FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    CONSTRAINT chk_clientes_dni CHECK (dni IS NULL OR CHAR_LENGTH(dni) = 8)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

CREATE TABLE conductores (
    user_id INT NOT NULL,
    dni VARCHAR(8) NULL,
    placa VARCHAR(7) NULL,
    PRIMARY KEY (user_id),
    CONSTRAINT uq_conductores_dni UNIQUE (dni),
    CONSTRAINT fk_conductores_user FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    CONSTRAINT chk_conductores_dni CHECK (dni IS NULL OR CHAR_LENGTH(dni) = 8),
    CONSTRAINT chk_conductores_placa CHECK (placa IS NULL OR CHAR_LENGTH(placa) = 7),
    INDEX ix_conductores_placa (placa)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

INSERT INTO clientes (user_id)
SELECT id FROM users WHERE role = 'passenger'
AND NOT EXISTS (SELECT 1 FROM clientes WHERE clientes.user_id = users.id);

INSERT INTO conductores (user_id)
SELECT id FROM users WHERE role = 'driver'
AND NOT EXISTS (SELECT 1 FROM conductores WHERE conductores.user_id = users.id);
