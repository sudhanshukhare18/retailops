import json
import os

from database import pool


BASE_DIR = os.path.dirname(
    os.path.dirname(
        os.path.abspath(__file__)
    )
)

RULES_PATH = os.path.join(
    BASE_DIR,
    "resources",
    "business_rules.json"
)


def load_business_rules():

    with open(
        RULES_PATH,
        "r",
        encoding="utf-8"
    ) as file:

        return json.load(file)


def generate_bill(customer_mobile: str):

    rules = load_business_rules()

    with pool.connection() as conn:

        try:

            with conn.cursor() as cur:

                # ======================================
                # 1. FIND CUSTOMER
                # ======================================

                cur.execute("""
                    SELECT
                        id,
                        name,
                        mobile,
                        email,
                        lifetime_profit
                    FROM customers
                    WHERE mobile = %s
                    FOR UPDATE
                """, (customer_mobile,))

                customer = cur.fetchone()

                if not customer:

                    return {
                        "success": False,
                        "message": "Customer not found"
                    }

                customer_id = customer[0]

                # ======================================
                # 2. FIND ACTIVE CART
                # ======================================

                cur.execute("""
                    SELECT id
                    FROM carts
                    WHERE customer_id = %s
                    AND status = 'ACTIVE'
                    FOR UPDATE
                """, (customer_id,))

                cart = cur.fetchone()

                if not cart:

                    return {
                        "success": False,
                        "message": "No active cart found"
                    }

                cart_id = cart[0]

                # ======================================
                # 3. GET CART ITEMS
                # ======================================

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
                        ON ci.product_id = p.id

                    WHERE ci.cart_id = %s

                    FOR UPDATE
                """, (cart_id,))

                cart_items = cur.fetchall()

                if not cart_items:

                    return {
                        "success": False,
                        "message": "Cart is empty"
                    }

                # ======================================
                # 4. CALCULATE ORDER
                # ======================================

                items = []

                total_amount = 0
                order_profit = 0

                for item in cart_items:

                    product_id = item[0]
                    quantity = item[1]
                    product_name = item[2]
                    selling_price = float(item[3])
                    cost_price = float(item[4])
                    stock = item[5]

                    # ------------------------------
                    # STOCK VALIDATION
                    # ------------------------------

                    if quantity > stock:

                        raise ValueError(
                            f"Insufficient stock for "
                            f"{product_name}. "
                            f"Available: {stock}"
                        )

                    item_total = (
                        selling_price *
                        quantity
                    )

                    item_profit = (
                        selling_price -
                        cost_price
                    ) * quantity

                    total_amount += item_total

                    order_profit += item_profit

                    items.append({

                        "product_id": product_id,

                        "name": product_name,

                        "quantity": quantity,

                        "selling_price":
                            selling_price,

                        "item_total":
                            round(item_total, 2),

                        "profit":
                            round(item_profit, 2)
                    })

                # ======================================
                # 5. LOYALTY CHECK
                # ======================================

                lifetime_profit = float(
                    customer[4]
                )

                loyalty_enabled = rules[
                    "loyalty_program"
                ]["enabled"]

                loyalty_threshold = rules[
                    "loyalty_program"
                ]["minimum_lifetime_profit"]

                discount_percentage = rules[
                    "loyalty_program"
                ][
                    "discount_percentage_of_current_order_profit"
                ]

                loyalty_eligible = (
                    loyalty_enabled
                    and
                    lifetime_profit >=
                    loyalty_threshold
                )

                discount = 0

                if loyalty_eligible:

                    discount = (
                        order_profit *
                        discount_percentage /
                        100
                    )

                # ======================================
                # 6. REMAINING PROFIT
                # ======================================

                remaining_profit = (
                    order_profit -
                    discount
                )

                # ======================================
                # 7. DELIVERY
                # ======================================

                free_delivery_threshold = rules[
                    "free_delivery"
                ][
                    "minimum_remaining_profit"
                ]

                if (
                    remaining_profit >=
                    free_delivery_threshold
                ):

                    delivery_status = rules[
                        "delivery"
                    ]["free_status"]

                else:

                    delivery_status = rules[
                        "delivery"
                    ]["default_status"]

                # ======================================
                # 8. FINAL AMOUNT
                # ======================================

                final_amount = (
                    total_amount -
                    discount
                )

                # ======================================
                # 9. CREATE ORDER
                # ======================================

                cur.execute("""
                    INSERT INTO orders
                    (
                        customer_id,
                        total_amount,
                        discount,
                        final_amount,
                        order_profit,
                        delivery_status
                    )

                    VALUES
                    (%s, %s, %s, %s, %s, %s)

                    RETURNING id
                """, (

                    customer_id,

                    total_amount,

                    discount,

                    final_amount,

                    remaining_profit,

                    delivery_status
                ))

                order_id = cur.fetchone()[0]

                # ======================================
                # 10. CREATE ORDER ITEMS
                # ======================================

                for item in items:

                    cur.execute("""
                        INSERT INTO order_items
                        (
                            order_id,
                            product_id,
                            quantity,
                            selling_price,
                            profit
                        )

                        VALUES
                        (%s, %s, %s, %s, %s)
                    """, (

                        order_id,

                        item["product_id"],

                        item["quantity"],

                        item["selling_price"],

                        item["profit"]
                    ))

                    # ==================================
                    # UPDATE STOCK
                    # ==================================

                    cur.execute("""
                        UPDATE products

                        SET stock =
                            stock - %s

                        WHERE id = %s
                    """, (

                        item["quantity"],

                        item["product_id"]
                    ))

                # ======================================
                # 11. UPDATE CUSTOMER PROFIT
                # ======================================

                cur.execute("""
                    UPDATE customers

                    SET lifetime_profit =
                        lifetime_profit + %s

                    WHERE id = %s
                """, (

                    remaining_profit,

                    customer_id
                ))

                # ======================================
                # 12. CLOSE CART
                # ======================================

                cur.execute("""
                    UPDATE carts

                    SET status = 'CHECKED_OUT',
                        updated_at =
                            CURRENT_TIMESTAMP

                    WHERE id = %s
                """, (cart_id,))

                # ======================================
                # 13. COMMIT EVERYTHING
                # ======================================

            conn.commit()

            # ==========================================
            # RETURN BILL
            # ==========================================

            return {

                "success": True,

                "order_id": order_id,

                "customer": {
                    "name": customer[1],
                    "mobile": customer[2],
                    "email": customer[3]
                },

                "items": items,

                "total_amount": round(
                    total_amount,
                    2
                ),

                "order_profit_before_discount":
                    round(
                        order_profit,
                        2
                    ),

                "loyalty_eligible":
                    loyalty_eligible,

                "loyalty_discount":
                    round(
                        discount,
                        2
                    ),

                "remaining_profit":
                    round(
                        remaining_profit,
                        2
                    ),

                "final_amount":
                    round(
                        final_amount,
                        2
                    ),

                "delivery_status":
                    delivery_status,

                "message":
                    "Bill generated successfully"
            }

        except Exception as error:

            conn.rollback()

            return {
                "success": False,
                "message": str(error)
            }