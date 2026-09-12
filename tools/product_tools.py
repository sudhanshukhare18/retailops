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
                ORDER BY name
            """, (f"%{name}%",))

            products = cur.fetchall()

    return {
        "success": True,
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
            "message": "Product not found"
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
            "message": "Product not found"
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