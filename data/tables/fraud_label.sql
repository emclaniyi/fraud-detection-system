CREATE TABLE fraud_label(
	trx_id INT PRIMARY KEY REFERENCES transactions(trx_id),
	is_fraud BOOLEAN NOT NULL DEFAULT FALSE,
	label_source VARCHAR(20) NOT NULL,
	fraud_type VARCHAR(50),
	labelling_ts TIMESTAMPTZ,
	notes TEXT
)
