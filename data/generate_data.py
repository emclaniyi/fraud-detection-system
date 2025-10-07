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

    def generate_kyc_submissions(self):
        """Generate KYC submissions with risk scores"""
        for user in self.users:
            credit_score_bucket = np.random.choice(
                ['poor', 'fair', 'good', 'excellent', None],
                p=[0.15, 0.25, 0.35, 0.20, 0.05]
            )
            base_risk = random.randint(0, 100)
            if credit_score_bucket in ['poor', None]:
                base_risk += random.randint(20, 40)

            id_num = random.choice(self.stolen_ids) if random.random() < 0.05 else f"ID{user['user_id']:08d}"
            user_devices = [d for d in self.devices if d['user_id'] == user['user_id']]
            id_type = random.choice(['Personalausweis', 'Reisepass', 'Residence Permit', 'eID Card'])
            doc_issue_country = fake.country() if id_type == 'Reisepass' else 'DE'

            kyc = {
                'submission_id': user['user_id'],
                'user_id': user['user_id'],
                'id_type': id_type,
                'doc_issue_country': doc_issue_country,
                'doc_issue_date': fake.date_between(start_date='-10y', end_date='-1y'),
                'selfie_hash_result': 'PASS' if random.random() > 0.1 else 'FAIL',
                'created_at': user['signup_ts'],
                'processed_at': user['signup_ts'] + timedelta(hours=random.randint(1, 48)),
                'status': random.choice(['approved', 'pending', 'rejected'], p=[0.85, 0.10, 0.05]),
                'risk_score': min(base_risk, 100),
                'reason': 'Auto-approved' if base_risk < 50 else 'Manual review required',
                'device_id': user_devices[0]['device_id'] if user_devices else None,
                'credit_score': credit_score_bucket
            }
            self.kyc_submissions.append(kyc)

        return pd.DataFrame(self.kyc_submissions)

    def generate_accounts(self):
        """Generate 1-2 accounts per user"""
        account_id = 1
        account_number = 1030102001

        for user in self.users:
            n_accounts = np.random.choice([1, 2], p=[0.7, 0.3])
            status_bucket = np.random.choice(
                ['active', 'inactive', 'dormant'],
                p=[0.7, 0.25, 0.05]
            )

            for _ in range(n_accounts):
                account = {
                    'account_id': account_id,
                    'user_id': user['user_id'],
                    'account_number': 'DE' + account_number,
                    'account_type': random.choice(['savings', 'current', 'loan']),
                    'currency': 'EURO',
                    'balance': round(random.uniform(1000, 500000), 2),
                    'open_ts': user['signup_ts'] + timedelta(days=random.randint(0, 7)),
                    'close_ts': None,
                    'status': status_bucket,
                    'last_activity_ts': user['signup_ts']
                }
                self.accounts.append(account)
                account_id += 1
                account_number += 1

        return pd.DataFrame(self.accounts)

    def generate_device_ip_history(self):
        """Generate IP history for devices"""
        history_id = 1
        for device in self.devices:
            n_ips = random.randint(1, 5)
            for _ in range(n_ips):
                entry = {
                    'id': history_id,
                    'device_id': device['device_id'],
                    'ip_address': fake.ipv4(),
                    'seen_ts': device['first_seen_ts'] + timedelta(days=random.randint(0, 100))
                }
                self.device_ip_history.append(entry)
                history_id += 1

        return pd.DataFrame(self.device_ip_history)

    def generate_transactions_batch(self, n_transactions=5000000):
        """Generate transactions in batches for memory efficiency"""
        # create user spending profiles
        user_profiles = {}
        for user in self.users:
            kyc = next(k for k in self.kyc_submissions if k['user_id'] == user['user_id'])
            risk_multiplier = 1.0

            if kyc['credit_score'] == 'poor':
                risk_multiplier = 2.0
            elif kyc['risk_score'] > 70:
                risk_multiplier = 1.5

            user_profiles[user['user_id']] = {
                'baseline_amount_mu': random.uniform(2000, 50000),
                'baseline_freq_per_day': random.uniform(0.5, 3.0) * risk_multiplier,
                'home_lat': random.uniform(47.0, 55.0),  # 🇩🇪 Germany lat range
                'home_long': random.uniform(6.0, 15.0),  # 🇩🇪 Germany long range
                'is_fraudster': random.random() < 0.03
            }

        trx_id = 1
        current_date = self.start_date
        transaction_batch = []
        recent_transactions = []

        while trx_id <= n_transactions and current_date <= self.end_date:
            user = random.choice(self.users)
            profile = user_profiles[user['user_id']]
            user_accounts = [a for a in self.accounts if a['user_id'] == user['user_id']]

            if not user_accounts:
                continue

            source_account = random.choice(user_accounts)
            user_devices = [d for d in self.devices if d['user_id'] == user['user_id']]

            hour = np.random.choice(range(24), p=self._hour_distribution())
            trx_ts = current_date + timedelta(hours=hour, minutes=random.randint(0, 59))

            amount = np.random.lognormal(np.log(profile['baseline_amount_mu']), 0.5)

            # Location logic
            if random.random() < 0.9:
                geo_lat = profile['home_lat'] + random.uniform(-0.1, 0.1)
                geo_long = profile['home_long'] + random.uniform(-0.1, 0.1)
            else:
                geo_lat = random.uniform(47.0, 55.0)
                geo_long = random.uniform(6.0, 15.0)

            device_ip = user_devices[0]['ip_address'] if user_devices else fake.ipv4()

            # Initialize
            is_fraud = False
            reason = None

            # -----------------------
            # 🇩🇪 FRAUD PATTERN RULES
            # -----------------------

            # Pattern 1: High velocity
            recent_trx = [t for t in recent_transactions[-50:]
                          if t['source_account_id'] == source_account['account_id'] and
                          (trx_ts - t['created_at']).total_seconds() < 3600]
            if len(recent_trx) > 5:
                is_fraud = True
                reason = "High transaction velocity within 1 hour."

            # Pattern 2: Amount spike
            user_trx_amounts = [t['amount'] for t in recent_transactions
                                if t['source_account_id'] == source_account['account_id']]
            if len(user_trx_amounts) > 10:
                z_score = (amount - np.mean(user_trx_amounts)) / (np.std(user_trx_amounts) + 1)
                if z_score > 3:
                    is_fraud = True
                    reason = "Amount spike above 3σ of normal pattern."

            # Pattern 3: Blacklisted IP
            if device_ip in self.blacklisted_ips:
                is_fraud = True
                reason = "Transaction from blacklisted IP."

            # Pattern 4: Known fraudster
            if profile['is_fraudster'] and random.random() < 0.4:
                is_fraud = True
                amount *= random.uniform(2, 5)
                reason = "Known fraudster activity."

            # 🇩🇪 Pattern 5: Structuring / Smurfing under €10K
            if 9000 <= amount < 10000 and len(recent_trx) >= 3:
                is_fraud = True
                reason = "Structuring — multiple transactions just below €10K threshold."

            # 🇩🇪 Pattern 6: Large cash movement near €50K
            if 45000 <= amount < 50000 and len(recent_trx) > 2:
                is_fraud = True
                reason = "Suspicious large movement just below €50K."

            # 🇩🇪 Pattern 7: Rapid turnaround (money in/out within 24h)
            if len(recent_trx) >= 2:
                prev_trx_1 = recent_trx[-1]
                prev_trx_2 = recent_trx[-2]
                time_diff = (prev_trx_1['created_at'] - prev_trx_2['created_at']).total_seconds()
                if time_diff < 86400 and prev_trx_2['trx_type'] == 'deposit' and prev_trx_1['trx_type'] == 'withdrawal':
                    is_fraud = True
                    reason = "Rapid fund movement — deposits withdrawn within 24h."

            # 🇩🇪 Pattern 8: Cross-border transaction to high-risk country
            country = random.choice(['DE', 'FR', 'NL', 'BE', 'AT', 'CH', 'RU', 'NG', 'UA', 'TR'])
            if country not in ['DE', 'FR', 'NL', 'BE', 'AT', 'CH'] and amount > 10000:
                is_fraud = True
                reason = f"Cross-border transfer to high-risk jurisdiction ({country})."

            # 🇩🇪 Pattern 9: Device/IP reuse
            if self.device_ip_history.count(device_ip) > 5:
                is_fraud = True
                reason = "Shared device/IP address across multiple users."

            # 🇩🇪 Pattern 10: Dormant account suddenly active
            account_age_days = (trx_ts - user['signup_ts']).days
            if len(recent_trx) == 1 and account_age_days > 180:
                is_fraud = True
                reason = "Dormant account suddenly active after long inactivity."

            # 🇩🇪 Pattern 11: Unusual currency / FX behavior
            currency = random.choice(['EUR', 'USD', 'GBP', 'NGN'])
            if currency != 'EUR' and amount > 20000:
                is_fraud = True
                reason = f"Foreign currency ({currency}) transaction above €20K."

            # 🇩🇪 Pattern 12: Failed KYC or mismatched selfie
            kyc_status = next((k['status'] for k in self.kyc_submissions if k['user_id'] == user['user_id']),
                              'approved')
            selfie_result = next(
                (k['selfie_hash_result'] for k in self.kyc_submissions if k['user_id'] == user['user_id']), 'PASS')
            if kyc_status == 'rejected' or selfie_result == 'FAIL':
                is_fraud = True
                reason = "KYC verification failed or mismatched selfie hash."

            # -----------------------
            # Create transaction
            # -----------------------
            transaction = {
                'trx_id': trx_id,
                'source_account_id': source_account['account_id'],
                'beneficiary_account_id': random.choice(self.accounts)['account_id'] if random.random() > 0.3 else None,
                'beneficiary_bank': random.choice(
                    ['Deutsche Bank', 'Commerzbank', 'N26', 'Revolut', 'Wise']) if random.random() > 0.5 else None,
                'trx_type': np.random.choice(['transfer', 'deposit', 'withdrawal'], p=[0.6, 0.2, 0.2]),
                'amount': round(amount, 2),
                'currency': currency,
                'channel': np.random.choice(['mobile', 'web', 'atm', 'branch'], p=[0.5, 0.3, 0.1, 0.1]),
                'status': 'completed' if not is_fraud or random.random() > 0.7 else 'blocked',
                'narration': fake.sentence(nb_words=6),
                'reference_id': f"REF{trx_id:010d}",
                'device_ip': device_ip,
                'geo_lat': geo_lat,
                'geo_long': geo_long,
                'country': country,
                'auth_result': True if not is_fraud else random.random() < 0.3,
                'created_at': trx_ts,
                'processed_at': trx_ts + timedelta(seconds=random.randint(1, 300)),
                'is_fraud': is_fraud,
                'reason': reason or "Normal transaction"
            }

            transaction_batch.append(transaction)
            recent_transactions.append(transaction)
            if len(recent_transactions) > 100:
                recent_transactions.pop(0)

            trx_id += 1

            # Yield batch
            if len(transaction_batch) >= self.batch_size:
                yield pd.DataFrame(transaction_batch)
                transaction_batch = []

            # Advance time occasionally
            if random.random() < 0.1:
                current_date += timedelta(hours=1)

        # Yield remaining transactions
        if transaction_batch:
            yield pd.DataFrame(transaction_batch)

    def _hour_distribution(self):
        """Create realistic hourly transaction distribution"""
        hours = np.array([
            0.01, 0.01, 0.01, 0.01, 0.01, 0.02,
            0.03, 0.05, 0.07, 0.08, 0.09, 0.09,
            0.08, 0.07, 0.06, 0.06, 0.07, 0.08,
            0.07, 0.06, 0.04, 0.03, 0.02, 0.01
        ])
        return hours / hours.sum()

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
