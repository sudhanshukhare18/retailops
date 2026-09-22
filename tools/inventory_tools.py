from database import pool
from tools.auth_tools import get_authenticated_user


# ============================================================
# AUTHORIZATION
# ============================================================

ALLOWED_ROLES = {"MANAGER", "OWNER"}


def _check_permission(auth_session_id: str):

    user = get_authenticated_user(auth_session_id)

    if not user.get("success"):
        return {
            "success": False,
            "message": "Authentication required."
        }

    current_user = user.get("user", {})
    role = current_user.get("role")

    if role not in ALLOWED_ROLES:
        return {
            "success": False,
            "message": (
                "Permission denied. "
                "Only MANAGER and OWNER can modify products."
            )
        }

    return {
        "success": True,
        "user": current_user
    }


# ============================================================
# ADD PRODUCT
# ============================================================

def add_product(
    auth_session_id: str,
    name: str,
    cost_price: float,
    selling_price: float,
    stock: int
):

    permission = _check_permission(auth_session_id)

    if not permission["success"]:
        return permission

    name = name.strip()

    if not name:
        return {
            "success": False,
            "message": "Product name cannot be empty."
        }

    if cost_price < 0:
        return {
            "success": False,
            "message": "Cost price cannot be negative."
        }

    if selling_price < 0:
        return {
            "success": False,
            "message": "Selling price cannot be negative."
        }

    if stock < 0:
        return {
            "success": False,
            "message": "Stock cannot be negative."
        }

    try:

        with pool.connection() as conn:

            with conn.cursor() as cur:

                # Check duplicate product
                cur.execute(
                    """
                    SELECT id
                    FROM products
                    WHERE LOWER(name) = LOWER(%s)
                    LIMIT 1
                    """,
                    (name,)
                )

                existing = cur.fetchone()

                if existing:
                    return {
                        "success": False,
                        "message": (
                            f"Product '{name}' already exists."
                        )
                    }

                cur.execute(
                    """
                    INSERT INTO products
                    (
                        name,
                        cost_price,
                        selling_price,
                        stock
                    )
                    VALUES
                    (
                        %s,
                        %s,
                        %s,
                        %s
                    )
                    RETURNING
                        id,
                        name,
                        cost_price,
                        selling_price,
                        stock
                    """,
                    (
                        name,
                        cost_price,
                        selling_price,
                        stock
                    )
                )

                row = cur.fetchone()

            conn.commit()

        return {
            "success": True,
            "message": (
                f"Product '{name}' added successfully."
            ),
            "product": {
                "id": row[0],
                "name": row[1],
                "cost_price": float(row[2]),
                "selling_price": float(row[3]),
                "stock": row[4]
            }
        }

    except Exception as e:

        return {
            "success": False,
            "message": f"Failed to add product: {str(e)}"
        }


# ============================================================
# UPDATE PRODUCT
# ============================================================

def update_product(
    auth_session_id: str,
    product_name: str,
    name: str | None = None,
    cost_price: float | None = None,
    selling_price: float | None = None,
    stock: int | None = None
):

    permission = _check_permission(auth_session_id)

    if not permission["success"]:
        return permission

    product_name = product_name.strip()

    if not product_name:
        return {
            "success": False,
            "message": "Product name is required."
        }

    try:

        with pool.connection() as conn:

            with conn.cursor() as cur:

                # Lock product
                cur.execute(
                    """
                    SELECT
                        id,
                        name,
                        cost_price,
                        selling_price,
                        stock
                    FROM products
                    WHERE LOWER(name) = LOWER(%s)
                    FOR UPDATE
                    """,
                    (product_name,)
                )

                product = cur.fetchone()

                if not product:
                    return {
                        "success": False,
                        "message": (
                            f"Product '{product_name}' "
                            "was not found."
                        )
                    }

                product_id = product[0]
                current_name = product[1]
                current_cost = float(product[2])
                current_selling = float(product[3])
                current_stock = product[4]

                new_name = (
                    name.strip()
                    if name is not None
                    else current_name
                )

                new_cost = (
                    cost_price
                    if cost_price is not None
                    else current_cost
                )

                new_selling = (
                    selling_price
                    if selling_price is not None
                    else current_selling
                )

                new_stock = (
                    stock
                    if stock is not None
                    else current_stock
                )

                # Validation
                if not new_name:
                    return {
                        "success": False,
                        "message": (
                            "Product name cannot be empty."
                        )
                    }

                if new_cost < 0:
                    return {
                        "success": False,
                        "message": (
                            "Cost price cannot be negative."
                        )
                    }

                if new_selling < 0:
                    return {
                        "success": False,
                        "message": (
                            "Selling price cannot be negative."
                        )
                    }

                if new_stock < 0:
                    return {
                        "success": False,
                        "message": (
                            "Stock cannot be negative."
                        )
                    }

                # Check duplicate name if renamed
                if new_name.lower() != current_name.lower():

                    cur.execute(
                        """
                        SELECT id
                        FROM products
                        WHERE LOWER(name) = LOWER(%s)
                          AND id != %s
                        LIMIT 1
                        """,
                        (
                            new_name,
                            product_id
                        )
                    )

                    duplicate = cur.fetchone()

                    if duplicate:
                        return {
                            "success": False,
                            "message": (
                                f"Another product named "
                                f"'{new_name}' already exists."
                            )
                        }

                cur.execute(
                    """
                    UPDATE products
                    SET
                        name = %s,
                        cost_price = %s,
                        selling_price = %s,
                        stock = %s
                    WHERE id = %s
                    RETURNING
                        id,
                        name,
                        cost_price,
                        selling_price,
                        stock
                    """,
                    (
                        new_name,
                        new_cost,
                        new_selling,
                        new_stock,
                        product_id
                    )
                )

                row = cur.fetchone()

            conn.commit()

        return {
            "success": True,
            "message": (
                f"Product '{current_name}' "
                "updated successfully."
            ),
            "product": {
                "id": row[0],
                "name": row[1],
                "cost_price": float(row[2]),
                "selling_price": float(row[3]),
                "stock": row[4]
            }
        }

    except Exception as e:

        return {
            "success": False,
            "message": (
                f"Failed to update product: {str(e)}"
            )
        }


# ============================================================
# DELETE PRODUCT
# ============================================================

def delete_product(
    auth_session_id: str,
    product_name: str
):

    permission = _check_permission(auth_session_id)

    if not permission["success"]:
        return permission

    product_name = product_name.strip()

    try:

        with pool.connection() as conn:

            with conn.cursor() as cur:

                cur.execute(
                    """
                    SELECT id, name
                    FROM products
                    WHERE LOWER(name) = LOWER(%s)
                    FOR UPDATE
                    """,
                    (product_name,)
                )

                product = cur.fetchone()

                if not product:
                    return {
                        "success": False,
                        "message": (
                            f"Product '{product_name}' "
                            "was not found."
                        )
                    }

                product_id = product[0]
                actual_name = product[1]

                # ------------------------------------------------
                # Protect historical orders
                # ------------------------------------------------

                cur.execute(
                    """
                    SELECT 1
                    FROM order_items
                    WHERE product_id = %s
                    LIMIT 1
                    """,
                    (product_id,)
                )

                if cur.fetchone():

                    return {
                        "success": False,
                        "message": (
                            f"Product '{actual_name}' cannot "
                            "be deleted because it is referenced "
                            "by historical orders."
                        )
                    }

                # ------------------------------------------------
                # Protect active carts
                # ------------------------------------------------

                cur.execute(
                    """
                    SELECT 1
                    FROM cart_items ci
                    JOIN carts c
                      ON c.id = ci.cart_id
                    WHERE ci.product_id = %s
                      AND c.status = 'ACTIVE'
                    LIMIT 1
                    """,
                    (product_id,)
                )

                if cur.fetchone():

                    return {
                        "success": False,
                        "message": (
                            f"Product '{actual_name}' is "
                            "currently present in an active "
                            "cart and cannot be deleted."
                        )
                    }

                # ------------------------------------------------
                # Delete
                # ------------------------------------------------

                cur.execute(
                    """
                    DELETE FROM products
                    WHERE id = %s
                    """,
                    (product_id,)
                )

            conn.commit()

        return {
            "success": True,
            "message": (
                f"Product '{actual_name}' "
                "deleted successfully."
            ),
            "product_id": product_id
        }

    except Exception as e:

        return {
            "success": False,
            "message": (
                f"Failed to delete product: {str(e)}"
            )
        }