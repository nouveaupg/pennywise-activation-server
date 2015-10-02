CREATE TABLE activation (activation_id INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
                           uuid CHAR(36) NOT NULL,
                           signature TEXT,
                           created TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                           UNIQUE(uuid));

CREATE TABLE bitcoin_pricing (serial MEDIUMINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
                             trailing_24hour_avg DECIMAL(7,2) NOT NULL,
                             currency_symbol CHAR(3),
                             timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP);

CREATE TABLE bitcoin_ledger (ledger_id INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
                               uuid CHAR(36) NOT NULL,
                               email VARCHAR(65),
                               bitcoin_address VARCHAR(35) NOT NULL,
                               bitcoin_confirmations INT UNSIGNED DEFAULT 0,
                               bitcoin_balance DOUBLE DEFAULT 0,
                               price_paid DOUBLE DEFAULT NULL,
                               refund_paid DOUBLE DEFAULT NULL,
                               refund_address VARCHAR(35),
                               activation_signature INT unsigned,
                               created TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                               paid TIMESTAMP,
                               refunded TIMESTAMP,
                               UNIQUE(uuid));
