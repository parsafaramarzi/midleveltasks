from fastapi import FastAPI, Header, HTTPException, status
from pydantic import BaseModel
from src.ledger.db import account_class, transaction_class, init_db, get_connection
from typing import Optional

init_db()

app = FastAPI()

class AccountModel(BaseModel):
    id: int
    name: str
    balance: float

class TransactionModel(BaseModel):
    account_source_id: Optional[int]
    account_destination_id: Optional[int]
    amount: float
    transaction_type: str

@app.post("/accounts/")
def create_account(account: AccountModel):
    new_account = account_class(account.name, account.balance, account.id)
    return {"message": "Account created successfully", "account": {"id": new_account.id, "name": new_account.name, "balance": new_account.balance}}

@app.get("/accounts/{account_id}", response_model=AccountModel)
def get_account(account_id: int):
    conn = get_connection()
    row = conn.execute("SELECT * FROM accounts WHERE id = ?", (account_id,)).fetchone()
    conn.close()
    if row:
        account = account_class(row[1], row[2], row[0])
        return {"id": account.id, "name": account.name, "balance": account.balance}
    else:
        return {"error": "Account not found"}

@app.post("/transactions/")
def create_transaction(transaction_data: TransactionModel, idempotency_key: str = Header(..., alias="Idempotency-Key")):
    account_source = None
    account_destination = None
    key_found = False

    #checking if the idempotency key already exists in the database
    conn = get_connection()
    key_row = conn.execute("SELECT * FROM idempotency_keys WHERE key = ?", (idempotency_key,)).fetchone()
    conn.close()

    if key_row:
        key_found = True

    if transaction_data.account_source_id is not None:
        conn = get_connection()
        source_row = conn.execute("SELECT * FROM accounts WHERE id = ?", (transaction_data.account_source_id,)).fetchone()
        conn.close()
        if source_row:
            account_source = account_class(source_row[1], source_row[2], source_row[0])
        else:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Source account not found")

    if transaction_data.account_destination_id is not None:
        conn = get_connection()
        destination_row = conn.execute("SELECT * FROM accounts WHERE id = ?", (transaction_data.account_destination_id,)).fetchone()
        conn.close()
        if destination_row:
            account_destination = account_class(destination_row[1], destination_row[2], destination_row[0])
        else:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Destination account not found")

    if key_found:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Idempotency key already exists")
    else:
        # do the transaction
        new_transaction = transaction_class(account_source, account_destination, transaction_data.amount, idempotency_key, transaction_data.transaction_type)
        new_transaction.process_transaction()

    return {"message": "Transaction processed successfully", "transaction": {"account_source_id": transaction_data.account_source_id, "account_destination_id": transaction_data.account_destination_id, "amount": transaction_data.amount, "transaction_type": transaction_data.transaction_type}}

@app.get("/transactions/{transaction_id}", response_model=TransactionModel)
def get_transaction(transaction_id: int):
    conn = get_connection()
    row = conn.execute("SELECT * FROM transactions WHERE id = ?", (transaction_id,)).fetchone()
    conn.close()
    if row:
        return {"id": row[0], "account_source_id": row[1], "account_destination_id": row[2], "amount": row[3], "transaction_type": row[4], "timestamp": row[5]}
    else:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Transaction not found")

@app.get("/transactions/", response_model=list[TransactionModel])
def get_transactions_by_account(account_id: int):
    conn = get_connection()
    rows = conn.execute("SELECT * FROM transactions WHERE account_source = ? OR account_destination = ?", (account_id, account_id)).fetchall()
    conn.close()
    transactions = []
    for row in rows:
        transactions.append({"id": row[0], "account_source_id": row[1], "account_destination_id": row[2], "amount": row[3], "transaction_type": row[4], "timestamp": row[5]})
    return transactions

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)