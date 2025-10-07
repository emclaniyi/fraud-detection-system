CREATE TABLE devices(
	device_id INT PRIMARY KEY,
	user_id INT NOT NULL REFERENCES users(user_id),
	device_type VARCHAR(50) NOT NULL,
	os VARCHAR(50) NOT NULL,
	first_seen_ts TIMESTAMPTZ DEFAULT now(),
	last_seen_ts TIMESTAMPTZ,
	ip_address INET
)
DROP TABLE devices CASCADE