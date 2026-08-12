from fastapi import FastAPI
from pydantic import BaseModel
from src.ledger.db import Account, transaction, init_db, conn, c

init_db()

app = FastAPI()

class AccountModel(BaseModel):
    id: int
    name: str
    balance: float

class TransactionModel(BaseModel):
    account_source_id: int | None
    account_destination_id: int | None
    amount: float
    transaction_type: str

@app.post("/accounts/")
def create_account(account: AccountModel):
    new_account = Account(account.name, account.balance, account.id)
    return {"message": "Account created successfully", "account": {"id": new_account.id, "name": new_account.name, "balance": new_account.balance}}

@app.get("/accounts/{account_id}", response_model=AccountModel)
def get_account(account_id: int):
    c.execute("SELECT * FROM accounts WHERE id = ?", (account_id,))
    row = c.fetchone()
    if row:
        account = Account(row[1], row[2], row[0])
        return {"id": account.id, "name": account.name, "balance": account.balance}
    else:
        return {"error": "Account not found"}

@app.post("/transactions/")
def create_transaction(transaction_data: TransactionModel):
    account_source = None
    account_destination = None

    if transaction_data.account_source_id is not None:
        c.execute("SELECT * FROM accounts WHERE id = ?", (transaction_data.account_source_id,))
        source_row = c.fetchone()
        if source_row:
            account_source = Account(source_row[1], source_row[2], source_row[0])
        else:
            return {"error": "Source account not found"}

    if transaction_data.account_destination_id is not None:
        c.execute("SELECT * FROM accounts WHERE id = ?", (transaction_data.account_destination_id,))
        destination_row = c.fetchone()
        if destination_row:
            account_destination = Account(destination_row[1], destination_row[2], destination_row[0])
        else:
            return {"error": "Destination account not found"}

    new_transaction = transaction(account_source, account_destination, transaction_data.amount, transaction_data.transaction_type)
    new_transaction.process_transaction()

    return {"message": "Transaction processed successfully", "transaction": {"account_source_id": transaction_data.account_source_id, "account_destination_id": transaction_data.account_destination_id, "amount": transaction_data.amount, "transaction_type": transaction_data.transaction_type}}

@app.get("/transactions/{transaction_id}", response_model=TransactionModel)
def get_transaction(transaction_id: int):
    c.execute("SELECT * FROM transactions WHERE id = ?", (transaction_id,))
    row = c.fetchone()
    if row:
        return {"id": row[0], "account_source_id": row[1], "account_destination_id": row[2], "amount": row[3], "transaction_type": row[4], "timestamp": row[5]}
    else:
        return {"error": "Transaction not found"}

@app.get("/transactions/", response_model=list[TransactionModel])
def get_transactions_by_account(account_id: int):
    c.execute("SELECT * FROM transactions WHERE account_source = ? OR account_destination = ?", (account_id, account_id))
    rows = c.fetchall()
    transactions = []
    for row in rows:
        transactions.append({"id": row[0], "account_source_id": row[1], "account_destination_id": row[2], "amount": row[3], "transaction_type": row[4], "timestamp": row[5]})
    return {"transactions": transactions}