CREATE SEQUENCE account_number_seq START 1030102001;
CREATE TABLE accounts(
	account_id SERIAL PRIMARY KEY,
	user_id INT NOT NULL REFERENCES users(user_id),
	account_number BIGINT UNIQUE NOT NULL DEFAULT nextval('account_number_seq'),
	account_type VARCHAR(20) NOT NULL, -- e.g. savings, current, loan
	currency CHAR(3) NOT NULL DEFAULT 'NGN',
	balance NUMERIC(12,2) DEFAULT 0.00,
	open_ts TIMESTAMPTZ DEFAULT now(),
	close_ts TIMESTAMPTZ,
	status VARCHAR(20) NOT NULL DEFAULT 'active', -- active, inactive, dormant, closed, frozen
	last_activity_ts TIMESTAMPTZ

)
--DROP SEQUENCE IF EXISTS account_number_seq;
--DROP TABLE accounts CASCADE 

-- 1. Drop existing sequence
DROP SEQUENCE IF EXISTS account_number_seq CASCADE;

-- 2. Recreate with MAXVALUE
CREATE SEQUENCE account_number_seq 
    START 1000000000
    MAXVALUE 9999999999
    NO CYCLE;

-- 3. Reconnect to accounts table
ALTER TABLE accounts 
    ALTER COLUMN account_number SET DEFAULT nextval('account_number_seq');

-- 4. Add safety constraint
ALTER TABLE accounts 
    ADD CONSTRAINT check_account_number_length 
    CHECK (account_number <= 9999999999);
