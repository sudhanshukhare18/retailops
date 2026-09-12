
from database import pool


def search_product(name: str):

    with pool.connection() as conn:

        with conn.cursor() as cur:

            cur.execute("""
                SELECT
                    id,
                    name,
                    category,
                    price,
                    stock
                FROM products
                WHERE name ILIKE %s
                ORDER BY
                    CASE
                        WHEN LOWER(name) = LOWER(%s) THEN 0
                        WHEN LOWER(name) LIKE LOWER(%s) THEN 1
                        ELSE 2
                    END,
                    name
            """, (
                f"%{name}%",
                name,
                f"{name}%"
            ))

            products = cur.fetchall()

    return {
        "success": True,
        "count": len(products),
        "products": [
            {
                "id": product[0],
                "name": product[1],
                "category": product[2],
                "price": float(product[3]),
                "stock": product[4]
            }
            for product in products
        ]
    }


def find_product_by_name(name: str):

    """
    Find a product using its natural name.

    First tries an exact case-insensitive match.
    If no exact match exists, performs a partial search.

    If exactly one partial match is found,
    that product is automatically selected.

    If multiple products are found,
    the caller is asked to choose one.
    """

    name = name.strip()

    if not name:

        return {
            "success": False,
            "message": "Product name cannot be empty."
        }

    with pool.connection() as conn:

        with conn.cursor() as cur:

            # ==========================================
            # 1. EXACT MATCH
            # ==========================================

            cur.execute("""
                SELECT
                    id,
                    name,
                    category,
                    price,
                    stock
                FROM products
                WHERE LOWER(name) = LOWER(%s)
                LIMIT 1
            """, (name,))

            product = cur.fetchone()

            if product:

                return {
                    "success": True,
                    "product": {
                        "id": product[0],
                        "name": product[1],
                        "category": product[2],
                        "price": float(product[3]),
                        "stock": product[4]
                    }
                }

            # ==========================================
            # 2. PARTIAL MATCH
            # ==========================================

            cur.execute("""
                SELECT
                    id,
                    name,
                    category,
                    price,
                    stock
                FROM products
                WHERE name ILIKE %s
                ORDER BY name
                LIMIT 10
            """, (f"%{name}%",))

            products = cur.fetchall()

    # ==========================================
    # NO MATCH
    # ==========================================

    if not products:

        return {
            "success": False,
            "message": f"Product '{name}' not found."
        }

    # ==========================================
    # ONE MATCH
    # ==========================================

    if len(products) == 1:

        product = products[0]

        return {
            "success": True,
            "product": {
                "id": product[0],
                "name": product[1],
                "category": product[2],
                "price": float(product[3]),
                "stock": product[4]
            }
        }

    # ==========================================
    # MULTIPLE MATCHES
    # ==========================================

    return {
        "success": False,
        "ambiguous": True,
        "message": (
            f"Multiple products found for '{name}'. "
            "Please select one."
        ),
        "products": [
            {
                "id": product[0],
                "name": product[1],
                "category": product[2],
                "price": float(product[3]),
                "stock": product[4]
            }
            for product in products
        ]
    }


def get_product_price(product_id: int):

    with pool.connection() as conn:

        with conn.cursor() as cur:

            cur.execute("""
                SELECT
                    id,
                    name,
                    price
                FROM products
                WHERE id = %s
            """, (product_id,))

            product = cur.fetchone()

    if not product:

        return {
            "success": False,
            "message": "Product not found."
        }

    return {
        "success": True,
        "product": {
            "id": product[0],
            "name": product[1],
            "price": float(product[2])
        }
    }


def check_stock(product_id: int):

    with pool.connection() as conn:

        with conn.cursor() as cur:

            cur.execute("""
                SELECT
                    id,
                    name,
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

    return {
        "success": True,
        "product": {
            "id": product[0],
            "name": product[1],
            "stock": product[2]
        }
    }


def get_all_product():

    with pool.connection() as conn:

        with conn.cursor() as cur:

            cur.execute("""
                SELECT
                    id,
                    name,
                    price,
                    stock,
                    category
                FROM products
                ORDER BY id;
            """)

            rows = cur.fetchall()

    items = []

    for row in rows:

        items.append({
            "product_id": row[0],
            "name": row[1],
            "unit_price": float(row[2]),
            "stock": row[3],
            "category": row[4]
        })

    return {
        "success": True,
        "products": items
    }

