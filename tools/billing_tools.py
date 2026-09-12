from decimal import Decimal
import json
import os

from database import pool
from tools.auth_tools import get_authenticated_user
from tools.session_tools import get_current_customer_session


# ============================================================
# GENERATE BILL
# ============================================================

def generate_bill(auth_session_id: str):

    # --------------------------------------------------------
    # AUTHENTICATION
    # --------------------------------------------------------

    user = get_authenticated_user(
        auth_session_id
    )

    if not user:

        return {
            "success": False,
            "message": "Authentication required."
        }


    # --------------------------------------------------------
    # CURRENT CUSTOMER SESSION
    # --------------------------------------------------------

    session = get_current_customer_session(
        auth_session_id
    )

    if not session["success"]:

        return session


    customer_id = session["customer"]["id"]

    cart_id = session["cart_id"]

    customer_session_id = (
        session["customer_session_id"]
    )


    # --------------------------------------------------------
    # BUSINESS RULES
    # --------------------------------------------------------

    base_dir = os.path.dirname(
        os.path.dirname(
            os.path.abspath(__file__)
        )
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


    # ========================================================
    # TRANSACTION
    # ========================================================

    with pool.connection() as conn:

        try:

            with conn.cursor() as cur:

                # ==================================================
                # LOCK CUSTOMER
                # ==================================================

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
                """, (
                    customer_id,
                ))

                customer = cur.fetchone()


                if not customer:

                    raise Exception(
                        "Customer not found."
                    )


                # ==================================================
                # LOCK CART
                # ==================================================

                cur.execute("""
                    SELECT
                        id,
                        status

                    FROM carts

                    WHERE id = %s

                    FOR UPDATE
                """, (
                    cart_id,
                ))

                cart = cur.fetchone()


                if not cart:

                    raise Exception(
                        "Cart not found."
                    )


                if cart[1] != "ACTIVE":

                    raise Exception(
                        "This cart has already "
                        "been checked out."
                    )


                # ==================================================
                # LOCK CART ITEMS + PRODUCTS
                # ==================================================

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
                """, (
                    cart_id,
                ))

                items = cur.fetchall()


                if not items:

                    raise Exception(
                        "Cannot generate bill "
                        "for an empty cart."
                    )


                # ==================================================
                # CALCULATIONS
                # ==================================================

                total_amount = Decimal("0")

                order_profit = Decimal("0")

                bill_items = []


                for item in items:

                    (
                        product_id,
                        quantity,
                        name,
                        price,
                        cost_price,
                        stock
                    ) = item


                    # ----------------------------------------------
                    # STOCK VALIDATION
                    # ----------------------------------------------

                    if stock < quantity:

                        raise Exception(
                            f"Insufficient stock for {name}. "
                            f"Available: {stock}"
                        )


                    item_total = (
                        price * quantity
                    )


                    # INTERNAL ONLY
                    item_profit = (
                        price - cost_price
                    ) * quantity


                    total_amount += item_total

                    order_profit += item_profit


                    # ----------------------------------------------
                    # CUSTOMER-SAFE ITEM
                    # ----------------------------------------------

                    bill_items.append({

                        "name":
                            name,

                        "quantity":
                            quantity,

                        "selling_price":
                            float(price),

                        "subtotal":
                            float(item_total)
                    })


                # ==================================================
                # LOYALTY CALCULATION
                # INTERNAL ONLY
                # ==================================================

                minimum_profit = Decimal(
                    str(
                        rules[
                            "loyalty_program"
                        ][
                            "minimum_lifetime_profit"
                        ]
                    )
                )


                discount_percentage = Decimal(
                    str(
                        rules[
                            "loyalty_program"
                        ][
                            "discount_percentage_of_current_order_profit"
                        ]
                    )
                )


                free_delivery_threshold = Decimal(
                    str(
                        rules[
                            "free_delivery"
                        ][
                            "minimum_remaining_profit"
                        ]
                    )
                )


                lifetime_profit = (
                    customer[4]
                )


                discount = Decimal("0")


                if lifetime_profit >= minimum_profit:

                    discount = (
                        order_profit
                        * discount_percentage
                        / Decimal("100")
                    )


                # INTERNAL ONLY
                remaining_profit = (
                    order_profit - discount
                )


                # ==================================================
                # DELIVERY STATUS
                # ==================================================

                if (
                    remaining_profit
                    >= free_delivery_threshold
                ):

                    delivery_status = (
                        rules[
                            "delivery"
                        ][
                            "free_status"
                        ]
                    )

                else:

                    delivery_status = (
                        rules[
                            "delivery"
                        ][
                            "default_status"
                        ]
                    )


                # ==================================================
                # FINAL CUSTOMER AMOUNT
                # ==================================================

                final_amount = (
                    total_amount - discount
                )


                # INTERNAL ONLY
                new_lifetime_profit = (
                    lifetime_profit
                    + remaining_profit
                )


                # ==================================================
                # CREATE ORDER
                # ==================================================

                cur.execute("""
                    INSERT INTO orders (
                        customer_id,
                        total_amount,
                        discount,
                        final_amount,
                        order_profit,
                        delivery_status
                    )

                    VALUES (
                        %s,
                        %s,
                        %s,
                        %s,
                        %s,
                        %s
                    )

                    RETURNING id, created_at
                """, (
                    customer_id,
                    total_amount,
                    discount,
                    final_amount,
                    order_profit,
                    delivery_status
                ))


                order_id, order_date = (
                    cur.fetchone()
                )


                # ==================================================
                # CREATE ORDER ITEMS
                # ==================================================

                for item in items:

                    (
                        product_id,
                        quantity,
                        name,
                        price,
                        cost_price,
                        stock
                    ) = item


                    # INTERNAL ONLY
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

                        VALUES (
                            %s,
                            %s,
                            %s,
                            %s,
                            %s
                        )
                    """, (
                        order_id,
                        product_id,
                        quantity,
                        price,
                        item_profit
                    ))


                    # ==================================================
                    # UPDATE INVENTORY
                    # ==================================================

                    cur.execute("""
                        UPDATE products

                        SET stock =
                            stock - %s

                        WHERE id = %s
                    """, (
                        quantity,
                        product_id
                    ))


                # ==================================================
                # UPDATE CUSTOMER INTERNAL PROFIT
                # ==================================================

                cur.execute("""
                    UPDATE customers

                    SET lifetime_profit = %s

                    WHERE id = %s
                """, (
                    new_lifetime_profit,
                    customer_id
                ))


                # ==================================================
                # CHECKOUT CART
                # ==================================================

                cur.execute("""
                    UPDATE carts

                    SET
                        status = 'CHECKED_OUT',
                        updated_at =
                            CURRENT_TIMESTAMP

                    WHERE id = %s
                """, (
                    cart_id,
                ))


                # ==================================================
                # COMPLETE CUSTOMER SESSION
                #
                # IMPORTANT:
                # Use customer_session_id,
                # NOT auth_session_id.
                # ==================================================

                cur.execute("""
                    UPDATE customer_sessions

                    SET
                        status = 'COMPLETED',
                        ended_at =
                            CURRENT_TIMESTAMP

                    WHERE id = %s

                      AND status = 'ACTIVE'
                """, (
                    customer_session_id,
                ))


                if cur.rowcount == 0:

                    raise Exception(
                        "Customer session could not "
                        "be completed."
                    )


            # ==================================================
            # COMMIT EVERYTHING
            # ==================================================

            conn.commit()


        except Exception as error:

            conn.rollback()

            return {
                "success": False,
                "message": str(error)
            }


    # ========================================================
    # CUSTOMER-SAFE RESPONSE
    #
    # NEVER RETURN:
    # cost_price
    # order_profit
    # lifetime_profit
    # remaining_profit
    # margin
    # ========================================================

    items_text_lines = []

    for item in bill_items:

        items_text_lines.append(
            f"{item['name']} "
            f"x {item['quantity']} "
            f"= ₹{item['subtotal']:.2f}"
        )


    items_text = "\n".join(
        items_text_lines
    )


    return {

        "success": True,

        "message":
            "Bill generated successfully.",

        "order_id":
            order_id,

        "order_date":
            order_date.isoformat(),

        "customer": {

            "name":
                customer[1],

            "email":
                customer[3]
        },

        "items":
            bill_items,

        "items_text":
            items_text,

        "subtotal":
            float(total_amount),

        "discount":
            float(discount),

        "final_amount":
            float(final_amount),

        "delivery_status":
            delivery_status,

        "cart_status":
            "CHECKED_OUT"
    }