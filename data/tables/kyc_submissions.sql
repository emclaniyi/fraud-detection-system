CREATE TABLE kyc_submissions(
	submission_id SERIAL PRIMARY KEY,
	user_id INT NOT NULL REFERENCES users(user_id),
	id_type VARCHAR(50),
	id_num_hash TEXT,
	doc_issue_country VARCHAR(50),
	doc_issue_date DATE,
	selfie_hash_result TEXT,
	created_at TIMESTAMPTZ DEFAULT now(),
	processed_at TIMESTAMPTZ,
	status VARCHAR(50),
	risk_score INT,
	reason TEXT,
	device_id INT NOT NULL REFERENCES devices(device_id),
	credit_score VARCHAR(50)
)