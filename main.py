import asyncio
import json
import random
from fastapi import FastAPI, Header, HTTPException
from pydantic import BaseModel #data vqalidation, to verify the data coming from external source
import psycopg2
from psycopg2.extras import RealDictCursor #return query results as dictionary
from psycopg2 import errors

app=FastAPI()

DB_CONFIG="dbname=payment_db user=postgres password=postgres123 host=localhost port=5432"

def get_db_connection():
    return psycopg2.connect(DB_CONFIG, cursor_factory=RealDictCursor)

class PaymentRequest(BaseModel):
    amount: float

#treat it as bg task-async
async def mock_charge_credit_card(amount: float):
    #pause for 1 sec to get approval from bank but handel other requests too
    # without await,entire program would freeze for 1 sec
    #await asyncio.sleep(1)
    #asyncio looks for all the paused tasks and timers
    return{
        "transactionId": f"txn_{random.randint(100000, 999999)}",
        "chargedAmount": amount,
        "status": "APPROVED"
    }

@app.post("/pay")#FastAPI route decorator that tells your web application: "Whenever a client sends an HTTP POST request to the /pay URL endpoint, run the Python function written directly beneath this decorator.
async def pay(payment: PaymentRequest, idempotency_key: str=Header(..., alias="Idempotency-Key"), X_user_id: str=Header(..., alias="X-User-ID")):
    
    try:
        conn=get_db_connection();
        with conn:
            with conn.cursor() as cur:
                try:
                    #insert with processing status
                    cur.execute("Insert into idempotency_keys (key, user_id, status) Values (%s, %s, 'PROCESSING')", (idempotency_key, X_user_id))
                except errors.UniqueViolation:
                    conn.rollback()

                    #check status of existing key
                    with conn.cursor() as check_cur:
                        check_cur.execute("SELECT status, response_payload from idempotency_keys where user_id=%s and key=%s", (X_user_id, idempotency_key))
                        record=check_cur.fetchone()

                        if record['status']=='SUCCESS':
                            print(f"[Idempotency Hit] Returning cached response for key: {idempotency_key}")
                            return {
                                "message": "Retrieved from cache (Duplicate request safely caught)",
                                "data": record['response_payload']
                            }
                        elif record['status'] == 'PROCESSING':
                            raise HTTPException(status_code=409, detail="Payment is already being processed. Please wait a moment.")
                #if duplicate entry does not exist
                print(f"[New Payment] Processing charge for user {X_user_id}, amount {payment.amount}...")
                gateway_response=await mock_charge_credit_card(payment.amount)
                cur.execute(
                    "INSERT INTO payments (user_id, amount, status) VALUES (%s, %s, 'SUCCESS')",
                    (X_user_id, payment.amount)
                )

                cur.execute(
                    "UPDATE idempotency_keys SET status = 'SUCCESS', response_payload = %s WHERE user_id = %s AND key = %s",
                    (json.dumps(gateway_response), X_user_id, idempotency_key)
                )
                return {
                    "message": "Payment processed successfully",
                    "data": gateway_response
                }
    #al errors other that duplicate id error
    except HTTPException as he:
        raise he
    except Exception as err:
        print("Payment processing error:", err)
        #500:something went wrong in internal server but no defined reason
        raise HTTPException(status_code=500, detail="Internal server error")
    finally:
        conn.close()