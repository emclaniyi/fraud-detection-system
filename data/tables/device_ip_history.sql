CREATE TABLE device_ip_history(
	id SERIAL PRIMARY KEY,
	device_id INT NOT NULL REFERENCES devices(device_id),
	ip_address INET NOT NULL,
	seen_ts TIMESTAMPTZ DEFAULT now()
)
