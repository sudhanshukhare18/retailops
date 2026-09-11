from database import pool


def get_or_create_active_cart(
    customer_mobile: str
):

    with pool.connection() as conn:

        with conn.cursor() as cur:

            # Find customer
            cur.execute("""
                SELECT id
                FROM customers
                WHERE mobile = %s
            """, (customer_mobile,))

            customer = cur.fetchone()

            if not customer:
                return None

            customer_id = customer[0]

            # Find active cart
            cur.execute("""
                SELECT id
                FROM carts
                WHERE customer_id = %s
                AND status = 'ACTIVE'
            """, (customer_id,))

            cart = cur.fetchone()

            if cart:
                return cart[0]

            # Create new cart
            cur.execute("""
                INSERT INTO carts
                (
                    customer_id,
                    status
                )
                VALUES (%s, 'ACTIVE')
                RETURNING id
            """, (customer_id,))

            cart_id = cur.fetchone()[0]

        conn.commit()

    return cart_id


def add_to_cart(
    customer_mobile: str,
    product_id: int,
    quantity: int = 1
):

    if quantity <= 0:

        return {
            "success": False,
            "message": "Quantity must be greater than zero"
        }

    cart_id = get_or_create_active_cart(
        customer_mobile
    )

    if not cart_id:

        return {
            "success": False,
            "message": "Customer not found"
        }

    with pool.connection() as conn:

        with conn.cursor() as cur:

            # Product
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
                    "message": "Product not found"
                }

            # Existing quantity
            cur.execute("""
                SELECT quantity
                FROM cart_items
                WHERE cart_id = %s
                AND product_id = %s
            """, (
                cart_id,
                product_id
            ))

            existing = cur.fetchone()

            current_quantity = (
                existing[0]
                if existing
                else 0
            )

            new_quantity = (
                current_quantity +
                quantity
            )

            # Stock check
            if new_quantity > product[3]:

                return {
                    "success": False,
                    "message": (
                        f"Only {product[3]} "
                        f"units available"
                    )
                }

            if existing:

                cur.execute("""
                    UPDATE cart_items
                    SET quantity = %s
                    WHERE cart_id = %s
                    AND product_id = %s
                """, (
                    new_quantity,
                    cart_id,
                    product_id
                ))

            else:

                cur.execute("""
                    INSERT INTO cart_items
                    (
                        cart_id,
                        product_id,
                        quantity
                    )
                    VALUES (%s, %s, %s)
                """, (
                    cart_id,
                    product_id,
                    quantity
                ))

            cur.execute("""
                UPDATE carts
                SET updated_at = CURRENT_TIMESTAMP
                WHERE id = %s
            """, (cart_id,))

        conn.commit()

    return {
        "success": True,
        "message": (
            f"{quantity} x {product[1]} "
            "added to cart"
        ),
        "cart_id": cart_id
    }


def remove_from_cart(
    customer_mobile: str,
    product_id: int
):

    cart_id = get_or_create_active_cart(
        customer_mobile
    )

    if not cart_id:

        return {
            "success": False,
            "message": "Customer not found"
        }

    with pool.connection() as conn:

        with conn.cursor() as cur:

            cur.execute("""
                DELETE FROM cart_items
                WHERE cart_id = %s
                AND product_id = %s
                RETURNING id
            """, (
                cart_id,
                product_id
            ))

            deleted = cur.fetchone()

        conn.commit()

    if not deleted:

        return {
            "success": False,
            "message": "Product not found in cart"
        }

    return {
        "success": True,
        "message": "Product removed from cart"
    }


def update_cart_quantity(
    customer_mobile: str,
    product_id: int,
    quantity: int
):

    if quantity <= 0:

        return remove_from_cart(
            customer_mobile,
            product_id
        )

    cart_id = get_or_create_active_cart(
        customer_mobile
    )

    if not cart_id:

        return {
            "success": False,
            "message": "Customer not found"
        }

    with pool.connection() as conn:

        with conn.cursor() as cur:

            # Check stock
            cur.execute("""
                SELECT
                    name,
                    stock
                FROM products
                WHERE id = %s
            """, (product_id,))

            product = cur.fetchone()

            if not product:

                return {
                    "success": False,
                    "message": "Product not found"
                }

            if quantity > product[1]:

                return {
                    "success": False,
                    "message": (
                        f"Only {product[1]} "
                        "units available"
                    )
                }

            cur.execute("""
                UPDATE cart_items
                SET quantity = %s
                WHERE cart_id = %s
                AND product_id = %s
                RETURNING id
            """, (
                quantity,
                cart_id,
                product_id
            ))

            updated = cur.fetchone()

        conn.commit()

    if not updated:

        return {
            "success": False,
            "message": "Product not found in cart"
        }

    return {
        "success": True,
        "message": "Cart quantity updated"
    }


def view_cart(customer_mobile: str):

    cart_id = get_or_create_active_cart(
        customer_mobile
    )

    if not cart_id:

        return {
            "success": False,
            "message": "Customer not found"
        }

    with pool.connection() as conn:

        with conn.cursor() as cur:

            cur.execute("""
                SELECT
                    p.id,
                    p.name,
                    p.price,
                    ci.quantity,
                    (p.price * ci.quantity)
                FROM cart_items ci
                JOIN products p
                    ON ci.product_id = p.id
                WHERE ci.cart_id = %s
                ORDER BY p.name
            """, (cart_id,))

            rows = cur.fetchall()

    items = []

    total = 0

    for row in rows:

        subtotal = float(row[4])

        total += subtotal

        items.append({
            "product_id": row[0],
            "name": row[1],
            "unit_price": float(row[2]),
            "quantity": row[3],
            "subtotal": subtotal
        })

    return {
        "success": True,
        "cart_id": cart_id,
        "items": items,
        "total": round(total, 2)
    }


def clear_cart(customer_mobile: str):

    cart_id = get_or_create_active_cart(
        customer_mobile
    )

    if not cart_id:

        return {
            "success": False,
            "message": "Customer not found"
        }

    with pool.connection() as conn:

        with conn.cursor() as cur:

            cur.execute("""
                DELETE FROM cart_items
                WHERE cart_id = %s
            """, (cart_id,))

            cur.execute("""
                UPDATE carts
                SET updated_at = CURRENT_TIMESTAMP
                WHERE id = %s
            """, (cart_id,))

        conn.commit()

    return {
        "success": True,
        "message": "Cart cleared"
    }