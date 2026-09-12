from decimal import Decimal
import json
import os

from database import pool
from tools.auth_tools import get_authenticated_user
from tools.session_tools import get_current_customer_session


def generate_bill(auth_session_id: str):

    user = get_authenticated_user(auth_session_id)

    if not user:

        return {
            "success": False,
            "message": "Authentication required."
        }

    session = get_current_customer_session(auth_session_id)

    if not session["success"]:

        return session

    customer_id = session["customer"]["id"]
    cart_id = session["cart_id"]

    base_dir = os.path.dirname(
        os.path.dirname(os.path.abspath(__file__))
    )

    rules_path = os.path.join(
        base_dir,
        "resources",
        "business_rules.json"
    )

    with open(
        rules_path,
        "r",
        encoding="utf-8"
    ) as file:

        rules = json.load(file)

    with pool.connection() as conn:

        try:

            with conn.cursor() as cur:

                # --------------------------------
                # LOCK CUSTOMER
                # --------------------------------

                cur.execute("""
                    SELECT
                        id,
                        name,
                        mobile,
                        email,
                        lifetime_profit
                    FROM customers
                    WHERE id = %s
                    FOR UPDATE
                """, (customer_id,))

                customer = cur.fetchone()

                if not customer:

                    raise Exception("Customer not found.")

                # --------------------------------
                # LOCK CART
                # --------------------------------

                cur.execute("""
                    SELECT id, status
                    FROM carts
                    WHERE id = %s
                    FOR UPDATE
                """, (cart_id,))

                cart = cur.fetchone()

                if not cart:

                    raise Exception("Cart not found.")

                if cart[1] != "ACTIVE":

                    raise Exception(
                        "This cart has already been checked out."
                    )

                # --------------------------------
                # LOCK CART ITEMS + PRODUCTS
                # --------------------------------

                cur.execute("""
                    SELECT
                        ci.product_id,
                        ci.quantity,
                        p.name,
                        p.price,
                        p.cost_price,
                        p.stock
                    FROM cart_items ci
                    JOIN products p
                        ON p.id = ci.product_id
                    WHERE ci.cart_id = %s
                    FOR UPDATE OF ci, p
                """, (cart_id,))

                items = cur.fetchall()

                if not items:

                    raise Exception(
                        "Cannot generate bill for an empty cart."
                    )

                total_amount = Decimal("0")
                order_profit = Decimal("0")

                bill_items = []

                # --------------------------------
                # CALCULATE
                # --------------------------------

                for item in items:

                    (
                        product_id,
                        quantity,
                        name,
                        price,
                        cost_price,
                        stock
                    ) = item

                    if stock < quantity:

                        raise Exception(
                            f"Insufficient stock for {name}. "
                            f"Available: {stock}"
                        )

                    item_total = price * quantity

                    item_profit = (
                        price - cost_price
                    ) * quantity

                    total_amount += item_total
                    order_profit += item_profit

                    bill_items.append({
                        "product_id": product_id,
                        "name": name,
                        "quantity": quantity,
                        "selling_price": float(price),
                        "profit": float(item_profit),
                        "subtotal": float(item_total)
                    })

                # --------------------------------
                # LOYALTY
                # --------------------------------

                minimum_profit = Decimal(
                    str(
                        rules["loyalty_program"]
                        ["minimum_lifetime_profit"]
                    )
                )

                discount_percentage = Decimal(
                    str(
                        rules["loyalty_program"]
                        ["discount_percentage_of_current_order_profit"]
                    )
                )

                free_delivery_threshold = Decimal(
                    str(
                        rules["free_delivery"]
                        ["minimum_remaining_profit"]
                    )
                )

                lifetime_profit = customer[4]

                discount = Decimal("0")

                if lifetime_profit >= minimum_profit:

                    discount = (
                        order_profit *
                        discount_percentage /
                        Decimal("100")
                    )

                remaining_profit = (
                    order_profit - discount
                )

                if remaining_profit >= free_delivery_threshold:

                    delivery_status = rules[
                        "delivery"
                    ]["free_status"]

                else:

                    delivery_status = rules[
                        "delivery"
                    ]["default_status"]

                final_amount = (
                    total_amount - discount
                )

                new_lifetime_profit = (
                    lifetime_profit +
                    remaining_profit
                )

                # --------------------------------
                # CREATE ORDER
                # --------------------------------

                cur.execute("""
                    INSERT INTO orders (
                        customer_id,
                        total_amount,
                        discount,
                        final_amount,
                        order_profit,
                        delivery_status
                    )
                    VALUES (%s, %s, %s, %s, %s, %s)
                    RETURNING id
                """, (
                    customer_id,
                    total_amount,
                    discount,
                    final_amount,
                    order_profit,
                    delivery_status
                ))

                order_id = cur.fetchone()[0]

                # --------------------------------
                # CREATE ORDER ITEMS
                # --------------------------------

                for item in items:

                    (
                        product_id,
                        quantity,
                        name,
                        price,
                        cost_price,
                        stock
                    ) = item

                    item_profit = (
                        price - cost_price
                    ) * quantity

                    cur.execute("""
                        INSERT INTO order_items (
                            order_id,
                            product_id,
                            quantity,
                            selling_price,
                            profit
                        )
                        VALUES (%s, %s, %s, %s, %s)
                    """, (
                        order_id,
                        product_id,
                        quantity,
                        price,
                        item_profit
                    ))

                    # --------------------------------
                    # UPDATE INVENTORY
                    # --------------------------------

                    cur.execute("""
                        UPDATE products
                        SET stock = stock - %s
                        WHERE id = %s
                    """, (
                        quantity,
                        product_id
                    ))

                # --------------------------------
                # UPDATE CUSTOMER PROFIT
                # --------------------------------

                cur.execute("""
                    UPDATE customers
                    SET lifetime_profit = %s
                    WHERE id = %s
                """, (
                    new_lifetime_profit,
                    customer_id
                ))

                # --------------------------------
                # CLOSE CART
                # --------------------------------

                cur.execute("""
                    UPDATE carts
                    SET
                        status = 'CHECKED_OUT',
                        updated_at = CURRENT_TIMESTAMP
                    WHERE id = %s
                """, (cart_id,))

                # --------------------------------
                # CLOSE CUSTOMER SESSION
                # --------------------------------

                cur.execute("""
                    UPDATE customer_sessions
                    SET
                        status = 'COMPLETED',
                        ended_at = CURRENT_TIMESTAMP
                    WHERE id = %s
                    AND status = 'ACTIVE'
                """, (auth_session_id,))

            conn.commit()

        except Exception as error:

            conn.rollback()

            return {
                "success": False,
                "message": str(error)
            }

    return {
        "success": True,
        "message": "Bill generated successfully.",

        "order_id": order_id,

        "customer": {
            "id": customer[0],
            "name": customer[1],
            "mobile": customer[2],
            "email": customer[3]
        },

        "items": bill_items,

        "total_amount": float(total_amount),

        "order_profit": float(order_profit),

        "loyalty_discount": float(discount),

        "remaining_profit": float(
            remaining_profit
        ),

        "final_amount": float(final_amount),

        "delivery_status": delivery_status,

        "updated_lifetime_profit": float(
            new_lifetime_profit
        ),

        "cart_status": "CHECKED_OUT"
    }