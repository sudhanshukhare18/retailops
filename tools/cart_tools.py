
from database import pool
from tools.auth_tools import get_authenticated_user
from tools.product_tools import find_product_by_name


# ============================================================
# GET CURRENT CUSTOMER CART
# ============================================================

def get_cart_from_session(auth_session_id: str):

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


# ============================================================
# ADD PRODUCT TO CART BY PRODUCT NAME
# ============================================================

def add_to_cart(
    auth_session_id: str,
    product_name: str,
    quantity: int = 1
):

    # --------------------------------------------------------
    # 1. GET CURRENT CUSTOMER SESSION
    # --------------------------------------------------------

    session, error = get_cart_from_session(
        auth_session_id
    )

    if error:
        return error

    # --------------------------------------------------------
    # 2. VALIDATE QUANTITY
    # --------------------------------------------------------

    if quantity <= 0:

        return {
            "success": False,
            "message": "Quantity must be greater than zero."
        }

    # --------------------------------------------------------
    # 3. FIND PRODUCT BY NAME
    # --------------------------------------------------------

    product_result = find_product_by_name(
        product_name
    )

    if not product_result["success"]:

        # This also handles ambiguous products.
        return product_result

    product = product_result["product"]

    product_id = product["id"]

    # --------------------------------------------------------
    # 4. CHECK STOCK
    # --------------------------------------------------------

    if product["stock"] < quantity:

        return {
            "success": False,
            "message": (
                f"Only {product['stock']} units of "
                f"{product['name']} are available."
            ),
            "product": product
        }

    # --------------------------------------------------------
    # 5. ADD TO CURRENT CUSTOMER'S CART
    # --------------------------------------------------------

    with pool.connection() as conn:

        with conn.cursor() as cur:

            # Check whether this product is already
            # present in the current customer's cart.

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

                new_quantity = (
                    existing[0] + quantity
                )

                # Make sure total cart quantity
                # does not exceed available stock.

                if new_quantity > product["stock"]:

                    return {
                        "success": False,
                        "message": (
                            f"Cannot add {quantity} more. "
                            f"Current cart quantity: "
                            f"{existing[0]}. "
                            f"Available stock: "
                            f"{product['stock']}."
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

                final_quantity = new_quantity

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

                final_quantity = quantity

            # ------------------------------------------------
            # UPDATE CART TIMESTAMP
            # ------------------------------------------------

            cur.execute("""
                UPDATE carts
                SET updated_at = CURRENT_TIMESTAMP
                WHERE id = %s
            """, (
                session["cart_id"],
            ))

        conn.commit()

    # --------------------------------------------------------
    # 6. RETURN RESULT
    # --------------------------------------------------------

    return {
        "success": True,
        "message": (
            f"{product['name']} added to cart."
        ),

        "customer_id": session["customer_id"],

        "cart_id": session["cart_id"],

        "product": {
            "id": product["id"],
            "name": product["name"],
            "category": product["category"],
            "unit_price": product["price"]
        },

        "quantity": final_quantity,

        "subtotal": (
            product["price"] * final_quantity
        )
    }


# ============================================================
# VIEW CURRENT CART
# ============================================================

def view_cart(auth_session_id: str):

    session, error = get_cart_from_session(
        auth_session_id
    )

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
            """, (
                session["cart_id"],
            ))

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


# ============================================================
# REMOVE PRODUCT FROM CART
# ============================================================

def remove_from_cart(
    auth_session_id: str,
    product_id: int
):

    session, error = get_cart_from_session(
        auth_session_id
    )

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

            cur.execute("""
                UPDATE carts
                SET updated_at = CURRENT_TIMESTAMP
                WHERE id = %s
            """, (
                session["cart_id"],
            ))

        conn.commit()

    if deleted == 0:

        return {
            "success": False,
            "message": (
                "Product is not in the current cart."
            )
        }

    return {
        "success": True,
        "message": "Product removed from cart."
    }


# ============================================================
# UPDATE CART QUANTITY
# ============================================================

def update_cart_quantity(
    auth_session_id: str,
    product_id: int,
    quantity: int
):

    session, error = get_cart_from_session(
        auth_session_id
    )

    if error:
        return error

    if quantity <= 0:

        return {
            "success": False,
            "message": "Quantity must be greater than zero."
        }

    with pool.connection() as conn:

        with conn.cursor() as cur:

            # ------------------------------------------------
            # CHECK PRODUCT STOCK
            # ------------------------------------------------

            cur.execute("""
                SELECT
                    id,
                    name,
                    stock
                FROM products
                WHERE id = %s
            """, (
                product_id,
            ))

            product = cur.fetchone()

            if not product:

                return {
                    "success": False,
                    "message": "Product not found."
                }

            if quantity > product[2]:

                return {
                    "success": False,
                    "message": (
                        f"Only {product[2]} units of "
                        f"{product[1]} are available."
                    )
                }

            # ------------------------------------------------
            # UPDATE CART
            # ------------------------------------------------

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
                    "message": (
                        "Product is not in the current cart."
                    )
                }

            cur.execute("""
                UPDATE carts
                SET updated_at = CURRENT_TIMESTAMP
                WHERE id = %s
            """, (
                session["cart_id"],
            ))

        conn.commit()

    return {
        "success": True,
        "message": (
            f"Quantity for {product[1]} updated "
            f"to {quantity}."
        )
    }


# ============================================================
# CLEAR CURRENT CART
# ============================================================

def clear_cart(auth_session_id: str):

    session, error = get_cart_from_session(
        auth_session_id
    )

    if error:
        return error

    with pool.connection() as conn:

        with conn.cursor() as cur:

            cur.execute("""
                DELETE FROM cart_items
                WHERE cart_id = %s
            """, (
                session["cart_id"],
            ))

            cur.execute("""
                UPDATE carts
                SET updated_at = CURRENT_TIMESTAMP
                WHERE id = %s
            """, (
                session["cart_id"],
            ))

        conn.commit()

    return {
        "success": True,
        "message": "Current cart cleared."
    }

