CREATE TABLE users(
	user_id INT PRIMARY KEY,
	first_name VARCHAR(500) NOT NULL,
	last_name VARCHAR(500) NOT NULL,
	email VARCHAR(500) NOT NULL,
	phone_number VARCHAR(500) NOT NULL,
	gender VARCHAR(20),
	dob DATE NOT NULL,
	occupation TEXT,
	address TEXT,
	zipcode INT,
	city VARCHAR(500),
	state VARCHAR(500),
	country VARCHAR(500),
	signup_ts TIMESTAMPTZ,
	signup_device VARCHAR(500)
)
--DROP TABLE users CASCADE;
