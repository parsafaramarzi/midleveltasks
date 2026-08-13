import datetime
import sqlite3

def get_connection():
    return sqlite3.connect("transaction_ledger.db")

def init_db():
    conn = sqlite3.connect("transaction_ledger.db")
    conn.execute('''CREATE TABLE IF NOT EXISTS accounts
                 (id INTEGER PRIMARY KEY, name TEXT, balance INTEGER)''')
    conn.execute('''CREATE TABLE IF NOT EXISTS transactions
                 (id INTEGER PRIMARY KEY, account_source INTEGER, account_destination INTEGER, idempotency_key TEXT UNIQUE,
                  amount INTEGER, transaction_type TEXT, timestamp DATETIME)''')
    conn.commit()
    conn.close()

accounts = []
class account_class():
    def __init__(self, name, balance, id):
        conn = get_connection()
        self.id = id
        self.name = name
        self.balance = balance
        conn.execute("INSERT OR REPLACE INTO accounts (id, name, balance) VALUES (?, ?, ?)", (self.id, self.name, self.balance))
        conn.commit()
        conn.close()

    def deposit(self, amount):
        conn = get_connection()
        conn.execute("UPDATE accounts SET balance = balance + ? WHERE id = ?", (amount, self.id))
        conn.commit()
        conn.close()
        self.balance += amount
        return self.balance

    def withdraw(self, amount):
        if amount > self.balance:
            return "Insufficient funds"
        else:
            conn = get_connection()
            conn.execute("UPDATE accounts SET balance = balance - ? WHERE id = ?", (amount, self.id))
            conn.commit()
            conn.close()
            self.balance -= amount
            return self.balance

    def transfer(self, amount, destination_account):
        if amount > self.balance:
            return "Insufficient funds"
        conn = get_connection()
        try:
            conn.execute("UPDATE accounts SET balance = balance - ? WHERE id = ?", (amount, self.id))
            conn.execute("UPDATE accounts SET balance = balance + ? WHERE id = ?", (amount, destination_account.id))
            conn.commit()
            conn.close()
            self.balance -= amount
            destination_account.balance += amount
        except Exception:
            conn.rollback()
            conn.close()
            raise
        return self.balance

    def get_balance(self):
        return self.balance

transactions = []
class transaction_class():
    def __init__(self, account_source, account_destination, idempotency_key, amount, transaction_type):
        self.account_source = account_source
        self.account_destination = account_destination
        self.idempotency_key = idempotency_key
        self.amount = amount
        self.transaction_type = transaction_type
        self.timestamp = datetime.datetime.now()
        conn = get_connection()
        conn.execute("INSERT INTO transactions (account_source, account_destination, idempotency_key, amount, transaction_type, timestamp) VALUES (?, ?, ?, ?, ?, ?)", (self.account_source.id if self.account_source else None, self.account_destination.id if self.account_destination else None, self.idempotency_key, self.amount, self.transaction_type, self.timestamp))
        conn.commit()
        conn.close()

    def process_transaction(self):
        if self.transaction_type == "deposit":
            return self.account_destination.deposit(self.amount)
        elif self.transaction_type == "withdraw":
            return self.account_source.withdraw(self.amount)
        elif self.transaction_type == "transfer":
            return self.account_source.transfer(self.amount, self.account_destination)
        else:
            return "Invalid transaction type"

if __name__ == "__main__":
    # Create accounts
    account1 = account_class("Alice", 1000, 1)
    account2 = account_class("Bob", 500, 2)
    accounts.append(account1)
    accounts.append(account2)

    # Perform transactions
    transaction1 = transaction_class(None, account1, 200, "deposit")
    transaction2 = transaction_class(account1, None, 150, "withdraw")
    transaction3 = transaction_class(account1, account2, 300, "transfer")

    transactions.append(transaction1)
    transactions.append(transaction2)
    transactions.append(transaction3)

    # Process transactions
    for t in transactions:
        result = t.process_transaction()
        print(f"Transaction: {t.transaction_type}, Amount: {t.amount}, Result: {result}, Timestamp: {t.timestamp}")