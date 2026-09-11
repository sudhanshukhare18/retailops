from psycopg_pool import ConnectionPool

from config import DATABASE_URL


pool = ConnectionPool(
    conninfo=DATABASE_URL,
    min_size=0,
    max_size=10,
    
)


def get_connection():
    return pool.connection()


def initialize_database():

    with pool.connection() as conn:

        with conn.cursor() as cur:

            # ==========================================
            # CUSTOMERS
            # ==========================================

            cur.execute("""
                CREATE TABLE IF NOT EXISTS customers (

                    id SERIAL PRIMARY KEY,

                    name VARCHAR(100) NOT NULL,

                    mobile VARCHAR(20)
                        UNIQUE NOT NULL,

                    email VARCHAR(255) NOT NULL,

                    lifetime_profit NUMERIC(12, 2)
                        NOT NULL DEFAULT 0,

                    created_at TIMESTAMP
                        DEFAULT CURRENT_TIMESTAMP
                );
            """)

            # ==========================================
            # PRODUCTS
            # ==========================================

            cur.execute("""
                CREATE TABLE IF NOT EXISTS products (

                    id SERIAL PRIMARY KEY,

                    name VARCHAR(150) NOT NULL,

                    category VARCHAR(100)
                        NOT NULL,

                    price NUMERIC(12, 2)
                        NOT NULL,

                    cost_price NUMERIC(12, 2)
                        NOT NULL,

                    stock INTEGER
                        NOT NULL DEFAULT 0,

                    created_at TIMESTAMP
                        DEFAULT CURRENT_TIMESTAMP
                );
            """)

            # ==========================================
            # CARTS
            # ==========================================

            cur.execute("""
                CREATE TABLE IF NOT EXISTS carts (

                    id SERIAL PRIMARY KEY,

                    customer_id INTEGER NOT NULL,

                    status VARCHAR(20)
                        NOT NULL DEFAULT 'ACTIVE',

                    created_at TIMESTAMP
                        DEFAULT CURRENT_TIMESTAMP,

                    updated_at TIMESTAMP
                        DEFAULT CURRENT_TIMESTAMP,

                    CONSTRAINT fk_cart_customer

                        FOREIGN KEY(customer_id)
                        REFERENCES customers(id)

                        ON DELETE CASCADE
                );
            """)

            # ==========================================
            # CART ITEMS
            # ==========================================

            cur.execute("""
                CREATE TABLE IF NOT EXISTS cart_items (

                    id SERIAL PRIMARY KEY,

                    cart_id INTEGER NOT NULL,

                    product_id INTEGER NOT NULL,

                    quantity INTEGER NOT NULL
                        CHECK (quantity > 0),

                    CONSTRAINT fk_cart

                        FOREIGN KEY(cart_id)
                        REFERENCES carts(id)

                        ON DELETE CASCADE,

                    CONSTRAINT fk_cart_product

                        FOREIGN KEY(product_id)
                        REFERENCES products(id)
                );
            """)

            # ==========================================
            # ORDERS
            # ==========================================

            cur.execute("""
                CREATE TABLE IF NOT EXISTS orders (

                    id SERIAL PRIMARY KEY,

                    customer_id INTEGER NOT NULL,

                    total_amount NUMERIC(12, 2)
                        NOT NULL,

                    discount NUMERIC(12, 2)
                        NOT NULL DEFAULT 0,

                    final_amount NUMERIC(12, 2)
                        NOT NULL,

                    order_profit NUMERIC(12, 2)
                        NOT NULL,

                    delivery_status VARCHAR(50)
                        NOT NULL,

                    created_at TIMESTAMP
                        DEFAULT CURRENT_TIMESTAMP,

                    CONSTRAINT fk_order_customer

                        FOREIGN KEY(customer_id)
                        REFERENCES customers(id)
                );
            """)

            # ==========================================
            # ORDER ITEMS
            # ==========================================

            cur.execute("""
                CREATE TABLE IF NOT EXISTS order_items (

                    id SERIAL PRIMARY KEY,

                    order_id INTEGER NOT NULL,

                    product_id INTEGER NOT NULL,

                    quantity INTEGER NOT NULL,

                    selling_price NUMERIC(12, 2)
                        NOT NULL,

                    profit NUMERIC(12, 2)
                        NOT NULL,

                    CONSTRAINT fk_order

                        FOREIGN KEY(order_id)
                        REFERENCES orders(id)

                        ON DELETE CASCADE,

                    CONSTRAINT fk_order_product

                        FOREIGN KEY(product_id)
                        REFERENCES products(id)
                );
            """)

            # ==========================================
            # ACTIVE CART INDEX
            # ==========================================

            cur.execute("""
                CREATE UNIQUE INDEX IF NOT EXISTS
                unique_active_customer_cart

                ON carts(customer_id)

                WHERE status = 'ACTIVE';
            """)

        conn.commit()


def seed_sample_data():

    with pool.connection() as conn:

        with conn.cursor() as cur:

            # ==========================================
            # CUSTOMERS
            # ==========================================

            cur.execute(
                "SELECT COUNT(*) FROM customers"
            )

            customer_count = cur.fetchone()[0]

            if customer_count == 0:

                cur.execute("""
                    INSERT INTO customers
                    (
                        name,
                        mobile,
                        email,
                        lifetime_profit
                    )

                    VALUES
                    (%s, %s, %s, %s),
                    (%s, %s, %s, %s),
                    (%s, %s, %s, %s)
                """, (

                    "Rahul Sharma",
                    "9876543210",
                    "rahul@example.com",
                    12000,

                    "Aman Verma",
                    "9123456780",
                    "aman@example.com",
                    3500,

                    "Priya Singh",
                    "9988776655",
                    "priya@example.com",
                    8500
                ))

            # ==========================================
            # PRODUCTS
            # ==========================================

            cur.execute(
                "SELECT COUNT(*) FROM products"
            )

            product_count = cur.fetchone()[0]

            if product_count == 0:

                cur.execute("""
                    INSERT INTO products
                    (
                        name,
                        category,
                        price,
                        cost_price,
                        stock
                    )

                    VALUES
                    (%s, %s, %s, %s, %s),
                    (%s, %s, %s, %s, %s),
                    (%s, %s, %s, %s, %s),
                    (%s, %s, %s, %s, %s),
                    (%s, %s, %s, %s, %s)
                """, (

                    "Samsung 55 inch",
                    "Television",
                    55000,
                    47000,
                    10,

                    "LG 43 inch",
                    "Television",
                    42000,
                    35000,
                    8,

                    "Sony Soundbar",
                    "Audio",
                    18000,
                    13000,
                    6,

                    "Boat Headphones",
                    "Audio",
                    2500,
                    1600,
                    15,

                    "Samsung Galaxy A55",
                    "Mobile",
                    38000,
                    32000,
                    12
                ))

        conn.commit()