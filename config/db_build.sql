-- schema v2 - added refund table and changed bitcoin value storage type to integer

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
bitcoin_balance BIGINT UNSIGNED DEFAULT 0,
price_paid BIGINT UNSIGNED DEFAULT NULL,
refund_paid BIGINT UNSIGNED DEFAULT NULL,
refund_address VARCHAR(35),
activation_signature INT unsigned,
created TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
paid TIMESTAMP,
refunded TIMESTAMP,
UNIQUE(uuid));

CREATE TABLE refunds (refund_id INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
btc_address VARCHAR(35) NOT NULL,
refund_tx_confirmations INT UNSIGNED DEFAULT 0,
refund_value_int64 BIGINT UNSIGNED NOT NULL,
refund_txid CHAR(64) DEFAULT NULL,
refund_type ENUM("automatic","manual"),
created TIMESTAMP DEFAULT CURRENT_TIMESTAMP);
