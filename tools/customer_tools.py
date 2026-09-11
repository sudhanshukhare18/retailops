from database import pool


def find_customer(mobile: str):

    with pool.connection() as conn:

        with conn.cursor() as cur:

            cur.execute("""
                SELECT
                    id,
                    name,
                    mobile,
                    email,
                    lifetime_profit
                FROM customers
                WHERE mobile = %s
            """, (mobile,))

            customer = cur.fetchone()

    if not customer:

        return {
            "success": False,
            "message": "Customer not found"
        }

    return {
        "success": True,
        "customer": {
            "id": customer[0],
            "name": customer[1],
            "mobile": customer[2],
            "email": customer[3],
            "lifetime_profit": float(customer[4])
        }
    }


def get_customer_details(mobile: str):

    return find_customer(mobile)


def get_customer_lifetime_profit(mobile: str):

    result = find_customer(mobile)

    if not result["success"]:
        return result

    return {
        "success": True,
        "customer": result["customer"]["name"],
        "lifetime_profit": result[
            "customer"
        ]["lifetime_profit"]
    }