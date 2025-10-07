CREATE TABLE transactions(
	trx_id SERIAL PRIMARY KEY,
	source_account_id INT NOT NULL REFERENCES accounts(account_id),
	beneficiary_account_id  INT REFERENCES accounts(account_id),
	beneficiary_bank VARCHAR(100),
	trx_type VARCHAR(20) NOT NULL, -- transfer, deposit, withdrawal
	amount NUMERIC(12,2) NOT NULL,
	currency CHAR(3) NOT NULL DEFAULT 'NGN',
	channel VARCHAR(50), -- mobile, web, ...
    status VARCHAR(20) NOT NULL DEFAULT 'pending',
    narration TEXT,
    reference_id VARCHAR(50) UNIQUE,
	device_ip INET,
	geo_lat DOUBLE PRECISION NOT NULL,
	geo_long DOUBLE PRECISION NOT NULL,
	country CHAR(5) DEFAULT 'NG',
	auth_result BOOLEAN DEFAULT 'FALSE',
    created_at TIMESTAMPTZ DEFAULT now(),
    processed_at TIMESTAMPTZ,
    is_fraud BOOLEAN DEFAULT FALSE
)
--DROP TABLE transactions CASCADE