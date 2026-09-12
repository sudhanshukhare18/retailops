from database import pool
from tools.auth_tools import get_authenticated_user


def get_cart_from_session(auth_session_id):

    user = get_authenticated_user(auth_session_id)

    if not user:

        return None, {
            "success": False,
            "message": "Authentication required."
        }

    with pool.connection() as conn:

        with conn.cursor() as cur:

            cur.execute("""
                SELECT
                    cs.customer_id,
                    cs.cart_id
                FROM customer_sessions cs
                JOIN carts c
                    ON c.id = cs.cart_id
                WHERE cs.auth_session_id = %s
                AND cs.status = 'ACTIVE'
                AND c.status = 'ACTIVE'
            """, (auth_session_id,))

            row = cur.fetchone()

    if not row:

        return None, {
            "success": False,
            "message": (
                "No active customer session. "
                "Start a customer session first."
            )
        }

    return {
        "customer_id": row[0],
        "cart_id": row[1]
    }, None


def add_to_cart(
    auth_session_id: str,
    product_id: int,
    quantity: int = 1
):

    session, error = get_cart_from_session(auth_session_id)

    if error:
        return error

    if quantity <= 0:

        return {
            "success": False,
            "message": "Quantity must be greater than zero."
        }

    with pool.connection() as conn:

        with conn.cursor() as cur:

            cur.execute("""
                SELECT
                    id,
                    name,
                    price,
                    stock
                FROM products
                WHERE id = %s
            """, (product_id,))

            product = cur.fetchone()

            if not product:

                return {
                    "success": False,
                    "message": "Product not found."
                }

            if product[3] < quantity:

                return {
                    "success": False,
                    "message": (
                        f"Only {product[3]} units available."
                    )
                }

            cur.execute("""
                SELECT quantity
                FROM cart_items
                WHERE cart_id = %s
                AND product_id = %s
            """, (
                session["cart_id"],
                product_id
            ))

            existing = cur.fetchone()

            if existing:

                new_quantity = existing[0] + quantity

                if new_quantity > product[3]:

                    return {
                        "success": False,
                        "message": (
                            f"Cannot add {quantity}. "
                            f"Only {product[3]} units available."
                        )
                    }

                cur.execute("""
                    UPDATE cart_items
                    SET quantity = %s
                    WHERE cart_id = %s
                    AND product_id = %s
                """, (
                    new_quantity,
                    session["cart_id"],
                    product_id
                ))

            else:

                cur.execute("""
                    INSERT INTO cart_items (
                        cart_id,
                        product_id,
                        quantity
                    )
                    VALUES (%s, %s, %s)
                """, (
                    session["cart_id"],
                    product_id,
                    quantity
                ))

            cur.execute("""
                UPDATE carts
                SET updated_at = CURRENT_TIMESTAMP
                WHERE id = %s
            """, (session["cart_id"],))

        conn.commit()

    return {
        "success": True,
        "message": "Product added to cart.",
        "customer_id": session["customer_id"],
        "cart_id": session["cart_id"],
        "product": product[1],
        "quantity_added": quantity
    }


def view_cart(auth_session_id: str):

    session, error = get_cart_from_session(auth_session_id)

    if error:
        return error

    with pool.connection() as conn:

        with conn.cursor() as cur:

            cur.execute("""
                SELECT
                    p.id,
                    p.name,
                    p.price,
                    ci.quantity
                FROM cart_items ci
                JOIN products p
                    ON p.id = ci.product_id
                WHERE ci.cart_id = %s
                ORDER BY p.name
            """, (session["cart_id"],))

            rows = cur.fetchall()

    items = []
    total = 0

    for row in rows:

        product_id = row[0]
        name = row[1]
        price = float(row[2])
        quantity = row[3]

        subtotal = price * quantity
        total += subtotal

        items.append({
            "product_id": product_id,
            "name": name,
            "unit_price": price,
            "quantity": quantity,
            "subtotal": subtotal
        })

    return {
        "success": True,
        "customer_id": session["customer_id"],
        "cart_id": session["cart_id"],
        "items": items,
        "total": total
    }


def remove_from_cart(
    auth_session_id: str,
    product_id: int
):

    session, error = get_cart_from_session(auth_session_id)

    if error:
        return error

    with pool.connection() as conn:

        with conn.cursor() as cur:

            cur.execute("""
                DELETE FROM cart_items
                WHERE cart_id = %s
                AND product_id = %s
            """, (
                session["cart_id"],
                product_id
            ))

            deleted = cur.rowcount

        conn.commit()

    if deleted == 0:

        return {
            "success": False,
            "message": "Product is not in the current cart."
        }

    return {
        "success": True,
        "message": "Product removed from cart."
    }


def update_cart_quantity(
    auth_session_id: str,
    product_id: int,
    quantity: int
):

    session, error = get_cart_from_session(auth_session_id)

    if error:
        return error

    if quantity <= 0:

        return {
            "success": False,
            "message": "Quantity must be greater than zero."
        }

    with pool.connection() as conn:

        with conn.cursor() as cur:

            cur.execute("""
                SELECT stock
                FROM products
                WHERE id = %s
            """, (product_id,))

            product = cur.fetchone()

            if not product:

                return {
                    "success": False,
                    "message": "Product not found."
                }

            if quantity > product[0]:

                return {
                    "success": False,
                    "message": (
                        f"Only {product[0]} units are available."
                    )
                }

            cur.execute("""
                UPDATE cart_items
                SET quantity = %s
                WHERE cart_id = %s
                AND product_id = %s
            """, (
                quantity,
                session["cart_id"],
                product_id
            ))

            if cur.rowcount == 0:

                return {
                    "success": False,
                    "message": "Product is not in the current cart."
                }

        conn.commit()

    return {
        "success": True,
        "message": "Cart quantity updated."
    }


def clear_cart(auth_session_id: str):

    session, error = get_cart_from_session(auth_session_id)

    if error:
        return error

    with pool.connection() as conn:

        with conn.cursor() as cur:

            cur.execute("""
                DELETE FROM cart_items
                WHERE cart_id = %s
            """, (session["cart_id"],))

        conn.commit()

    return {
        "success": True,
        "message": "Current cart cleared."
    }