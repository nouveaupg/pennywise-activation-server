-- schema v3 - separated bitcoin irrelevant functionality

CREATE TABLE bitcoin_pricing (serial INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
trailing_24hour_avg DECIMAL(10,2) NOT NULL,
currency_symbol CHAR(3),
timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP);

CREATE TABLE bitcoin_ledger (ledger_id INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
uuid CHAR(36) NOT NULL,
email VARCHAR(65),
bitcoin_address VARCHAR(35) DEFAULT NULL,
bitcoin_confirmations INT UNSIGNED DEFAULT 0,
bitcoin_balance BIGINT UNSIGNED DEFAULT 0,
price_paid BIGINT UNSIGNED DEFAULT NULL,
refund_paid INT UNSIGNED DEFAULT NULL,
refund_address VARCHAR(35),
order_id INT unsigned,
created TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
paid TIMESTAMP,
refunded TIMESTAMP,
UNIQUE(uuid));

CREATE TABLE bitcoin_server_status (server_status_id INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
server_uuid CHAR(36),
getinfo_response TEXT,
status ENUM("normal","starting","error")
created TIMESTAMP DEFAULT CURRENT_TIMESTAMP);

CREATE TABLE deposit_address_queue (deposit_address_queue_id INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
btc_address VARCHAR(35) NOT NULL,
ledger_id INT UNSIGNED DEFAULT NULL,
assigned TIMESTAMP,
created TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
UNIQUE(btc_address));

CREATE TABLE withdrawals (withdrawal_id INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
btc_address VARCHAR(35) NOT NULL,
btc_value_int64 BIGINT UNSIGNED NOT NULL,
txid CHAR(64) DEFAULT NULL,
processed TIMESTAMP,
created TIMESTAMP DEFAULT CURRENT_TIMESTAMP);

CREATE TABLE refunds (refund_id INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
btc_address VARCHAR(35) NOT NULL,
refund_value_int64 BIGINT UNSIGNED NOT NULL,
refund_txid CHAR(64) DEFAULT NULL,
refund_type ENUM("automatic","manual"),
created TIMESTAMP DEFAULT CURRENT_TIMESTAMP);
