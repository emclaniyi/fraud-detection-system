import pandas as pd
import numpy as np
from faker import Faker
from datetime import datetime, timedelta
import random
from scipy import stats
import hashlib
import psycopg2
from psycopg2.extras import execute_batch

fake = Faker('de_DE')
np.random.seed(42)
random.seed(42)


class FraudDataGenerator:
    def __init__(self, n_users=50000, start_date='2023-01-01', end_date='2025-07-31'):
        self.n_users = n_users
        self.start_date = pd.to_datetime(start_date)
        self.end_date = pd.to_datetime(end_date)
        self.batch_size = 10000
        self.users = []
        self.accounts = []
        self.devices = []
        self.kyc_submissions = []
        self.transactions = []
        self.device_ip_history = []

        # blacklisted IPs and stolen IDs for fraud injection
        self.blacklisted_ips = [fake.ipv4() for _ in range(50)]
        self.stolen_ids = [f"STOLEN{i:06d}" for i in range(100)]

    def generate_users(self):
        """Generate userbase population with demographic info"""
        for i in range(1, self.n_users + 1):
            signup_ts = self._random_timestamp(self.start_date, self.end_date)
            if signup_ts.weekday() >= 5:  # weekend
                signup_ts = signup_ts - timedelta(days=random.randint(1, 2))

            user = {
                'user_id': i,
                'first_name': fake.first_name(),
                'last_name': fake.last_name(),
                'email': fake.email(),
                'phone_number': fake.phone_number()[:20],
                'gender': random.choice(['M', 'F']),
                'dob': fake.date_of_birth(minimum_age=18, maximum_age=80),
                'occupation': fake.job(),
                'address': fake.street_address(),
                'zipcode': random.randint(100000, 999999),
                'city': fake.city(),
                'state': fake.state(),
                'country': 'DE',
                'signup_ts': signup_ts,
                'signup_device': random.choice(['iOS', 'Android'])
            }

            self.users.append(user)
        return pd.DataFrame(self.users)

    def generate_devices(self):
        """Generate devices per user (1-3 devices)"""
        device_id = 1
        for user in self.users:
            n_devices = np.random.choice([1, 2, 3], p=[0.7, 0.25, 0.05])

            for _ in range(n_devices):
                device = {
                    'device_id': device_id,
                    'user_id': user['user_id'],
                    'device_type': random.choice(['mobile', 'tablet']),
                    'os': random.choice(['iOS', 'Android']),
                    'first_seen_ts': user['signup_ts'],
                    'last_seen_ts': user['signup_ts'] + timedelta(days=random.randint(1, 300)),
                    'ip_address': fake.ipv4()
                }
                self.devices.append(device)
                device_id += 1

        return pd.DataFrame(self.devices)

    def _random_timestamp(self, start, end):
        """Generate random timestamp between start and end"""
        delta = end - start
        random_seconds = random.randint(0, int(delta.total_seconds()))
        return start + timedelta(seconds=random_seconds)

    def _insert_dataframe(self, cursor, table_name, df):
        """Insert DataFrame into database table efficiently"""
        if len(df) == 0:
            return

        columns = df.columns.tolist()
        placeholders = ','.join(['%s'] * len(columns))
        insert_query = f"INSERT INTO {table_name} ({','.join(columns)}) VALUES ({placeholders})"

        records = [tuple(row) for row in df.to_numpy()]
        execute_batch(cursor, insert_query, records, page_size=1000)

    def push_to_db(self, conn_string):
        """Push data directly to PostgreSQL database in batches"""

        conn = psycopg2.connect(conn_string)
        cursor = conn.cursor()

        # Generate and insert users
        print("📊 Generating and inserting users...")
        users_df = self.generate_users()
        self._insert_dataframe(cursor, 'users', users_df)
        conn.commit()
        print(f"   ✓ Inserted {len(users_df):,} users\n")

        # Generate and insert devices
        print("📱 Generating and inserting devices...")
        devices_df = self.generate_devices()
        self._insert_dataframe(cursor, 'devices', devices_df)
        conn.commit()
        print(f"   ✓ Inserted {len(devices_df):,} devices\n")


if __name__ == "__main__":
    # Database connection string
    # Format: postgresql://username:password@host:port/database
    conn_string = "postgresql://postgres:postgres@localhost:5432/boxyapp"

    # Create generator for 5 million transactions
    generator = FraudDataGenerator(
        n_users=500,  # 50K users
        start_date='2023-01-01',  # 2-year period
        end_date='2024-12-31'
    )

    # Push to database
    generator.push_to_db(conn_string)
