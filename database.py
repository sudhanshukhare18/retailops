from psycopg_pool import ConnectionPool

from config import DATABASE_URL


# ============================================================
# DATABASE CONNECTION POOL
# ============================================================

pool = ConnectionPool(
    conninfo=DATABASE_URL,
    min_size=0,
    max_size=10,
)


# ============================================================
# CONNECTION
# ============================================================

def get_connection():
    return pool.connection()


# ============================================================
# CLOSE DATABASE
# ============================================================

def close_database():
    pool.close()


# ============================================================
# INITIALIZE DATABASE
# ============================================================

def initialize_database():

    with pool.connection() as conn:

        with conn.cursor() as cur:

            # ==================================================
            # CUSTOMERS
            # ==================================================

            cur.execute("""
                CREATE TABLE IF NOT EXISTS customers (

                    id SERIAL PRIMARY KEY,

                    name VARCHAR(150) NOT NULL,

                    mobile VARCHAR(20) UNIQUE NOT NULL,

                    email VARCHAR(255),

                    lifetime_profit NUMERIC(12,2)
                        DEFAULT 0,

                    created_at TIMESTAMP
                        DEFAULT CURRENT_TIMESTAMP
                );
            """)

            # ==================================================
            # PRODUCTS
            # ==================================================

            cur.execute("""
                CREATE TABLE IF NOT EXISTS products (

                    id SERIAL PRIMARY KEY,

                    name VARCHAR(200) NOT NULL,

                    category VARCHAR(100),

                    price NUMERIC(12,2) NOT NULL,

                    cost_price NUMERIC(12,2) NOT NULL,

                    stock INTEGER NOT NULL DEFAULT 0,

                    created_at TIMESTAMP
                        DEFAULT CURRENT_TIMESTAMP
                );
            """)

            # ==================================================
            # CARTS
            # ==================================================

            cur.execute("""
                CREATE TABLE IF NOT EXISTS carts (

                    id SERIAL PRIMARY KEY,

                    customer_id INTEGER NOT NULL
                        REFERENCES customers(id),

                    status VARCHAR(30) NOT NULL
                        DEFAULT 'ACTIVE',

                    created_at TIMESTAMP
                        DEFAULT CURRENT_TIMESTAMP,

                    updated_at TIMESTAMP
                        DEFAULT CURRENT_TIMESTAMP
                );
            """)

            # ==================================================
            # CART ITEMS
            # ==================================================

            cur.execute("""
                CREATE TABLE IF NOT EXISTS cart_items (

                    id SERIAL PRIMARY KEY,

                    cart_id INTEGER NOT NULL
                        REFERENCES carts(id)
                        ON DELETE CASCADE,

                    product_id INTEGER NOT NULL
                        REFERENCES products(id),

                    quantity INTEGER NOT NULL
                        CHECK(quantity > 0),

                    UNIQUE(cart_id, product_id)
                );
            """)

            # ==================================================
            # ORDERS
            # ==================================================

            cur.execute("""
                CREATE TABLE IF NOT EXISTS orders (

                    id SERIAL PRIMARY KEY,

                    customer_id INTEGER NOT NULL
                        REFERENCES customers(id),

                    total_amount NUMERIC(12,2) NOT NULL,

                    discount NUMERIC(12,2)
                        DEFAULT 0,

                    final_amount NUMERIC(12,2) NOT NULL,

                    order_profit NUMERIC(12,2) NOT NULL,

                    delivery_status VARCHAR(50),

                    created_at TIMESTAMP
                        DEFAULT CURRENT_TIMESTAMP
                );
            """)

            # ==================================================
            # ORDER ITEMS
            # ==================================================

            cur.execute("""
                CREATE TABLE IF NOT EXISTS order_items (

                    id SERIAL PRIMARY KEY,

                    order_id INTEGER NOT NULL
                        REFERENCES orders(id)
                        ON DELETE CASCADE,

                    product_id INTEGER NOT NULL
                        REFERENCES products(id),

                    quantity INTEGER NOT NULL,

                    selling_price NUMERIC(12,2) NOT NULL,

                    profit NUMERIC(12,2) NOT NULL
                );
            """)

            # ==================================================
            # USERS
            # ==================================================

            cur.execute("""
                CREATE TABLE IF NOT EXISTS users (

                    id SERIAL PRIMARY KEY,

                    username VARCHAR(100)
                        UNIQUE NOT NULL,

                    password_hash TEXT NOT NULL,

                    role VARCHAR(30) NOT NULL
                        CHECK(
                            role IN (
                                'SALESPERSON',
                                'MANAGER',
                                'OWNER'
                            )
                        ),

                    created_at TIMESTAMP
                        DEFAULT CURRENT_TIMESTAMP
                );
            """)

            # ==================================================
            # AUTH SESSIONS
            # ==================================================

            cur.execute("""
                CREATE TABLE IF NOT EXISTS auth_sessions (

                    id UUID PRIMARY KEY,

                    user_id INTEGER NOT NULL
                        REFERENCES users(id)
                        ON DELETE CASCADE,

                    is_active BOOLEAN
                        DEFAULT TRUE,

                    created_at TIMESTAMP
                        DEFAULT CURRENT_TIMESTAMP,

                    last_used_at TIMESTAMP
                        DEFAULT CURRENT_TIMESTAMP
                );
            """)

            # ==================================================
            # CUSTOMER SESSIONS
            # ==================================================

            cur.execute("""
                CREATE TABLE IF NOT EXISTS customer_sessions (

                    id UUID PRIMARY KEY,

                    auth_session_id UUID NOT NULL
                        REFERENCES auth_sessions(id)
                        ON DELETE CASCADE,

                    customer_id INTEGER NOT NULL
                        REFERENCES customers(id),

                    cart_id INTEGER NOT NULL
                        REFERENCES carts(id),

                    status VARCHAR(30) NOT NULL
                        DEFAULT 'ACTIVE',

                    created_at TIMESTAMP
                        DEFAULT CURRENT_TIMESTAMP,

                    ended_at TIMESTAMP
                );
            """)

            # ==================================================
            # TASKS
            # MANAGER → OWNER WORKFLOW
            # ==================================================

            cur.execute("""
                CREATE TABLE IF NOT EXISTS tasks (

                    id SERIAL PRIMARY KEY,

                    title VARCHAR(255) NOT NULL,

                    description TEXT,

                    created_by INTEGER NOT NULL
                        REFERENCES users(id),

                    priority VARCHAR(20) NOT NULL
                        DEFAULT 'MEDIUM',

                    status VARCHAR(30) NOT NULL
                        DEFAULT 'PENDING_APPROVAL',

                    owner_comment TEXT,

                    created_at TIMESTAMP
                        DEFAULT CURRENT_TIMESTAMP,

                    updated_at TIMESTAMP
                        DEFAULT CURRENT_TIMESTAMP,

                    approved_at TIMESTAMP
                );
            """)

            # ==================================================
            # TASK STATUS CONSTRAINT
            # ==================================================

            cur.execute("""
                ALTER TABLE tasks
                DROP CONSTRAINT IF EXISTS
                tasks_status_check;
            """)

            cur.execute("""
                ALTER TABLE tasks
                ADD CONSTRAINT tasks_status_check
                CHECK (
                    status IN (
                        'PENDING_APPROVAL',
                        'APPROVED',
                        'REJECTED',
                        'COMPLETED'
                    )
                );
            """)

            # ==================================================
            # TASK PRIORITY CONSTRAINT
            # ==================================================

            cur.execute("""
                ALTER TABLE tasks
                DROP CONSTRAINT IF EXISTS
                tasks_priority_check;
            """)

            cur.execute("""
                ALTER TABLE tasks
                ADD CONSTRAINT tasks_priority_check
                CHECK (
                    priority IN (
                        'LOW',
                        'MEDIUM',
                        'HIGH',
                        'URGENT'
                    )
                );
            """)

            # ==================================================
            # UNIQUE ACTIVE CART
            # ==================================================

            cur.execute("""
                CREATE UNIQUE INDEX IF NOT EXISTS
                unique_active_customer_cart

                ON carts(customer_id)

                WHERE status = 'ACTIVE';
            """)

            # ==================================================
            # UNIQUE ACTIVE CUSTOMER SESSION
            # ==================================================

            cur.execute("""
                CREATE UNIQUE INDEX IF NOT EXISTS
                unique_active_customer_session

                ON customer_sessions(auth_session_id)

                WHERE status = 'ACTIVE';
            """)

            # ==================================================
            # PENDING TASK INDEX
            # ==================================================

            cur.execute("""
                CREATE INDEX IF NOT EXISTS
                idx_tasks_pending

                ON tasks(status)

                WHERE status = 'PENDING_APPROVAL';
            """)

        conn.commit()