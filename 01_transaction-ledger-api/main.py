import datetime
import sqlite3

conn = sqlite3.connect("transaction_ledger.db")
c = conn.cursor()

c.execute('''CREATE TABLE IF NOT EXISTS accounts
             (id INTEGER PRIMARY KEY, name TEXT, balance INTEGER)''')

c.execute('''CREATE TABLE IF NOT EXISTS transactions
             (id INTEGER PRIMARY KEY, account_source INTEGER, account_destination INTEGER, amount INTEGER, transaction_type TEXT, timestamp DATETIME)''')

conn.commit()

accounts = []
class account():
    def __init__(self, name, balance, id):
        self.id = id
        self.name = name
        self.balance = balance
        c.execute("INSERT OR REPLACE INTO accounts (id, name, balance) VALUES (?, ?, ?)", (self.id, self.name, self.balance))
        conn.commit()

    def deposit(self, amount):
        self.balance += amount
        c.execute("UPDATE accounts SET balance = ? WHERE id = ?", (self.balance, self.id))
        conn.commit()
        return self.balance

    def withdraw(self, amount):
        if amount > self.balance:
            return "Insufficient funds"
        else:
            self.balance -= amount
            c.execute("UPDATE accounts SET balance = ? WHERE id = ?", (self.balance, self.id))
            conn.commit()
            return self.balance

    def transfer(self, amount, destination_account):
        if amount > self.balance:
            return "Insufficient funds"
        else:
            self.balance -= amount
            destination_account.balance += amount
            c.execute("UPDATE accounts SET balance = ? WHERE id = ?", (self.balance, self.id))
            c.execute("UPDATE accounts SET balance = ? WHERE id = ?", (destination_account.balance, destination_account.id))
            conn.commit()
            return self.balance

    def get_balance(self):
        return self.balance

transactions = []
class transaction():
    def __init__(self, account_source, account_destination, amount, transaction_type):
        self.account_source = account_source
        self.account_destination = account_destination
        self.amount = amount
        self.transaction_type = transaction_type
        self.timestamp = datetime.datetime.now()
        c.execute("INSERT INTO transactions (account_source, account_destination, amount, transaction_type, timestamp) VALUES (?, ?, ?, ?, ?)", (self.account_source.id if self.account_source else None, self.account_destination.id if self.account_destination else None, self.amount, self.transaction_type, self.timestamp))
        conn.commit()
        
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
    account1 = account("Alice", 1000, 1)
    account2 = account("Bob", 500, 2)
    accounts.append(account1)
    accounts.append(account2)

    # Perform transactions
    transaction1 = transaction(None, account1, 200, "deposit")
    transaction2 = transaction(account1, None, 150, "withdraw")
    transaction3 = transaction(account1, account2, 300, "transfer")  # Invalid type

    transactions.append(transaction1)
    transactions.append(transaction2)
    transactions.append(transaction3)

    # Process transactions
    for t in transactions:
        result = t.process_transaction()
        print(f"Transaction: {t.transaction_type}, Amount: {t.amount}, Result: {result}, Timestamp: {t.timestamp}")