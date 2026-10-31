import asyncio
import httpx
import traceback

async def send_request(client, request_num, idempotency_key, user_id):
    try:
        response = await client.post(
            "http://localhost:8000/pay",
            json={"amount": 250.00},
            headers={
              "Idempotency-Key": idempotency_key,
                "X-User-ID": user_id
            },
            timeout=5.0
        )
        return {"requestNumber": request_num, "status": response.status_code, "data": response.json()}
    except Exception as e:
        # This will print the full technical error to your terminal
        return {"requestNumber": request_num, "status": "ERROR", "data": traceback.format_exc()}

async def run_test():
    idempotency_key = "python-test-key-998"
    user_id = "user_python_123"

    print("🚀 Firing 3 identical payment requests simultaneously...")
    
    async with httpx.AsyncClient() as client:
        tasks = [send_request(client, i + 1, idempotency_key, user_id) for i in range(3)]
        results = await asyncio.gather(*tasks)

    print("\n--- TEST RESULTS ---")
    for res in results:
        print(f"Request #{res['requestNumber']} -> HTTP Status: {res['status']}\nDetails:\n{res['data']}")

if __name__ == "__main__":
    asyncio.run(run_test())