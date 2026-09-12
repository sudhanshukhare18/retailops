import uuid

from database import pool
from tools.auth_tools import get_authenticated_user


def start_customer_session(
    auth_session_id: str,
    customer_name: str,
    mobile: str = None,
    email: str = None
):

    user = get_authenticated_user(auth_session_id)

    if not user:

        return {
            "success": False,
            "message": "Authentication required."
        }

    if user["role"] not in [
        "SALESPERSON",
        "MANAGER",
        "OWNER"
    ]:

        return {
            "success": False,
            "message": "You do not have permission."
        }

    with pool.connection() as conn:

        with conn.cursor() as cur:

            # --------------------------------
            # CLOSE PREVIOUS CUSTOMER SESSION
            # --------------------------------

            cur.execute("""
                UPDATE customer_sessions
                SET
                    status = 'COMPLETED',
                    ended_at = CURRENT_TIMESTAMP
                WHERE auth_session_id = %s
                AND status = 'ACTIVE'
            """, (auth_session_id,))

            # --------------------------------
            # FIND CUSTOMER
            # --------------------------------

            customer = None

            if mobile:

                cur.execute("""
                    SELECT
                        id,
                        name,
                        mobile,
                        email,
                        lifetime_profit
                    FROM customers
                    WHERE mobile = %s
                """, (mobile,))

                customer = cur.fetchone()

            # --------------------------------
            # IF CUSTOMER NOT FOUND
            # --------------------------------

            if not customer:

                # A mobile is required for permanent customer creation.
                if not mobile:

                    return {
                        "success": False,
                        "message": (
                            "New customer detected. "
                            "Please provide mobile number "
                            "before creating the permanent customer record."
                        )
                    }

                cur.execute("""
                    INSERT INTO customers (
                        name,
                        mobile,
                        email
                    )
                    VALUES (%s, %s, %s)
                    RETURNING
                        id,
                        name,
                        mobile,
                        email,
                        lifetime_profit
                """, (
                    customer_name,
                    mobile,
                    email
                ))

                customer = cur.fetchone()

            customer_id = customer[0]

            # --------------------------------
            # CREATE / GET ACTIVE CART
            # --------------------------------

            cur.execute("""
                SELECT id
                FROM carts
                WHERE customer_id = %s
                AND status = 'ACTIVE'
                FOR UPDATE
            """, (customer_id,))

            cart = cur.fetchone()

            if cart:

                cart_id = cart[0]

            else:

                cur.execute("""
                    INSERT INTO carts (
                        customer_id,
                        status
                    )
                    VALUES (%s, 'ACTIVE')
                    RETURNING id
                """)

                cart_id = cur.fetchone()[0]

            # --------------------------------
            # CREATE CUSTOMER SESSION
            # --------------------------------

            customer_session_id = uuid.uuid4()

            cur.execute("""
                INSERT INTO customer_sessions (
                    id,
                    auth_session_id,
                    customer_id,
                    cart_id,
                    status
                )
                VALUES (
                    %s,
                    %s,
                    %s,
                    %s,
                    'ACTIVE'
                )
            """, (
                customer_session_id,
                auth_session_id,
                customer_id,
                cart_id
            ))

        conn.commit()

    return {
        "success": True,
        "message": "Customer session started.",
        "customer_session_id": str(customer_session_id),
        "customer": {
            "id": customer[0],
            "name": customer[1],
            "mobile": customer[2],
            "email": customer[3],
            "lifetime_profit": float(customer[4])
        },
        "cart_id": cart_id
    }


def get_current_customer_session(auth_session_id: str):

    user = get_authenticated_user(auth_session_id)

    if not user:

        return {
            "success": False,
            "message": "Authentication required."
        }

    with pool.connection() as conn:

        with conn.cursor() as cur:

            cur.execute("""
                SELECT
                    cs.id,
                    cs.customer_id,
                    cs.cart_id,
                    c.name,
                    c.mobile,
                    c.email,
                    c.lifetime_profit
                FROM customer_sessions cs
                JOIN customers c
                    ON c.id = cs.customer_id
                WHERE cs.auth_session_id = %s
                AND cs.status = 'ACTIVE'
            """, (auth_session_id,))

            row = cur.fetchone()

    if not row:

        return {
            "success": False,
            "message": "No active customer session."
        }

    return {
        "success": True,
        "customer_session_id": str(row[0]),
        "customer": {
            "id": row[1],
            "name": row[3],
            "mobile": row[4],
            "email": row[5],
            "lifetime_profit": float(row[6])
        },
        "cart_id": row[2]
    }


def end_customer_session(auth_session_id: str):

    user = get_authenticated_user(auth_session_id)

    if not user:

        return {
            "success": False,
            "message": "Authentication required."
        }

    with pool.connection() as conn:

        with conn.cursor() as cur:

            cur.execute("""
                UPDATE customer_sessions
                SET
                    status = 'COMPLETED',
                    ended_at = CURRENT_TIMESTAMP
                WHERE auth_session_id = %s
                AND status = 'ACTIVE'
            """, (auth_session_id,))

            updated = cur.rowcount

        conn.commit()

    if updated == 0:

        return {
            "success": False,
            "message": "No active customer session."
        }

    return {
        "success": True,
        "message": "Customer session ended."
    }