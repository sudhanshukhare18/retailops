import uuid
import bcrypt

from database import pool


def hash_password(password: str) -> str:

    password_bytes = password.encode("utf-8")

    hashed = bcrypt.hashpw(
        password_bytes,
        bcrypt.gensalt()
    )

    return hashed.decode("utf-8")


def verify_password(password: str, password_hash: str) -> bool:

    return bcrypt.checkpw(
        password.encode("utf-8"),
        password_hash.encode("utf-8")
    )


def login(username: str, password: str):

    with pool.connection() as conn:

        with conn.cursor() as cur:

            cur.execute("""
                SELECT
                    id,
                    username,
                    password_hash,
                    role
                FROM users
                WHERE username = %s
            """, (username,))

            user = cur.fetchone()

            if not user:
                return {
                    "success": False,
                    "message": "Invalid username or password."
                }

            user_id, db_username, password_hash, role = user

            if not verify_password(password, password_hash):

                return {
                    "success": False,
                    "message": "Invalid username or password."
                }

            session_id = uuid.uuid4()

            cur.execute("""
                INSERT INTO auth_sessions (
                    id,
                    user_id
                )
                VALUES (%s, %s)
            """, (
                session_id,
                user_id
            ))

        conn.commit()

    return {
        "success": True,
        "message": "Authentication successful.",
        "session_id": str(session_id),
        "username": db_username,
        "role": role
    }


def logout(session_id: str):

    with pool.connection() as conn:

        with conn.cursor() as cur:

            cur.execute("""
                UPDATE auth_sessions
                SET is_active = FALSE
                WHERE id = %s
            """, (session_id,))

            if cur.rowcount == 0:

                return {
                    "success": False,
                    "message": "Session not found."
                }

        conn.commit()

    return {
        "success": True,
        "message": "Logged out successfully."
    }


def get_authenticated_user(session_id: str):

    with pool.connection() as conn:

        with conn.cursor() as cur:

            cur.execute("""
                SELECT
                    u.id,
                    u.username,
                    u.role
                FROM auth_sessions s
                JOIN users u
                    ON u.id = s.user_id
                WHERE s.id = %s
                AND s.is_active = TRUE
            """, (session_id,))

            user = cur.fetchone()

            if not user:

                return None

            cur.execute("""
                UPDATE auth_sessions
                SET last_used_at = CURRENT_TIMESTAMP
                WHERE id = %s
            """, (session_id,))

        conn.commit()

    return {
        "id": user[0],
        "username": user[1],
        "role": user[2]
    }