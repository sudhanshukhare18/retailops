import bcrypt

from database import pool


users = [
    {
        "username": "salesperson",
        "password": "sales123",
        "role": "SALESPERSON"
    },
    {
        "username": "manager",
        "password": "manager123",
        "role": "MANAGER"
    },
    {
        "username": "owner",
        "password": "owner123",
        "role": "OWNER"
    }
]


with pool.connection() as conn:

    with conn.cursor() as cur:

        for user in users:

            password_hash = bcrypt.hashpw(
                user["password"].encode("utf-8"),
                bcrypt.gensalt()
            ).decode("utf-8")

            cur.execute("""
                INSERT INTO users (
                    username,
                    password_hash,
                    role
                )
                VALUES (%s, %s, %s)
                ON CONFLICT (username)
                DO NOTHING
            """, (
                user["username"],
                password_hash,
                user["role"]
            ))

    conn.commit()


print("Users created successfully.")



pool.close()