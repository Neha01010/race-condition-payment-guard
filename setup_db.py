import psycopg2

def setup():
    conn=psycopg2.connect("dbname=payment_db user=postgres password=postgres123 host=localhost port=5432")#5432=addr for postgres
    cur=conn.cursor();

    cur.execute("""
        CREATE TABLE IF NOT EXISTS payments(
            id SERIAL PRIMARY KEY,
            user_id VARCHAR(255) NOT NULL,
            amount DECIMAL(10, 2) NOT NULL,
            status VARCHAR(50) NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP);

            CREATE TABLE IF NOT EXISTS idempotency_keys (
                id SERIAL PRIMARY KEY,
                key VARCHAR(255) NOT NULL,
                user_id VARCHAR(255) NOT NULL,
                status VARCHAR(50) NOT NULL,
                response_payload JSONB,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                CONSTRAINT unique_user_key UNIQUE (user_id, key)
            );
            """)
    conn.commit()
    cur.close()
    conn.close()
    print("Database created")

if __name__=="__main__":
    setup()
