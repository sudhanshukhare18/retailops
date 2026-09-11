import os

from fastmcp import FastMCP

from database import (
    initialize_database,
    seed_sample_data
)

from tools import (

    # Customer
    find_customer,
    get_customer_details,
    get_customer_lifetime_profit,

    # Product
    search_product,
    get_product_price,
    check_stock,

    # Cart
    add_to_cart,
    remove_from_cart,
    update_cart_quantity,
    view_cart,
    clear_cart,

    # Billing
    generate_bill
)


mcp = FastMCP("RetailOps")


# ==================================================
# CUSTOMER
# ==================================================

@mcp.tool()
def mcp_find_customer(mobile: str):
    """
    Find a customer using their mobile number.
    """
    return find_customer(mobile)


@mcp.tool()
def mcp_get_customer_details(mobile: str):
    """
    Retrieve customer details.
    """
    return get_customer_details(mobile)


@mcp.tool()
def mcp_get_customer_lifetime_profit(
    mobile: str
):
    """
    Retrieve customer's lifetime profit.
    """
    return get_customer_lifetime_profit(
        mobile
    )


# ==================================================
# PRODUCT
# ==================================================

@mcp.tool()
def mcp_search_product(name: str):
    """
    Search products by name.
    """
    return search_product(name)


@mcp.tool()
def mcp_get_product_price(
    product_id: int
):
    """
    Get product selling price.
    """
    return get_product_price(product_id)


@mcp.tool()
def mcp_check_stock(product_id: int):
    """
    Check product stock availability.
    """
    return check_stock(product_id)


# ==================================================
# CART
# ==================================================

@mcp.tool()
def mcp_add_to_cart(
    customer_mobile: str,
    product_id: int,
    quantity: int = 1
):
    """
    Add a product to the customer's
    persistent virtual cart.
    """
    return add_to_cart(
        customer_mobile,
        product_id,
        quantity
    )


@mcp.tool()
def mcp_remove_from_cart(
    customer_mobile: str,
    product_id: int
):
    """
    Remove a product from the cart.
    """
    return remove_from_cart(
        customer_mobile,
        product_id
    )


@mcp.tool()
def mcp_update_cart_quantity(
    customer_mobile: str,
    product_id: int,
    quantity: int
):
    """
    Update product quantity in the cart.
    """
    return update_cart_quantity(
        customer_mobile,
        product_id,
        quantity
    )


@mcp.tool()
def mcp_view_cart(
    customer_mobile: str
):
    """
    View customer's current cart.
    """
    return view_cart(customer_mobile)


@mcp.tool()
def mcp_clear_cart(
    customer_mobile: str
):
    """
    Clear customer's virtual cart.
    """
    return clear_cart(customer_mobile)


# ==================================================
# BILLING
# ==================================================

@mcp.tool()
def mcp_generate_bill(
    customer_mobile: str
):
    """
    Generate the final customer bill.

    Performs:
    - Customer validation
    - Cart validation
    - Stock validation
    - Price calculation
    - Profit calculation
    - Loyalty discount calculation
    - Delivery eligibility
    - Order creation
    - Order item creation
    - Inventory update
    - Customer lifetime profit update
    - Cart checkout
    """
    return generate_bill(
        customer_mobile
    )

@mcp.tool()
def mcp_health_check():
    """
    Check whether RetailOps MCP can connect
    to the PostgreSQL database.
    """

    from database import pool

    try:

        with pool.connection() as conn:

            with conn.cursor() as cur:

                cur.execute("SELECT 1")

                result = cur.fetchone()

        return {
            "success": True,
            "database": "PostgreSQL",
            "status": "CONNECTED"
        }

    except Exception as error:

        return {
            "success": False,
            "database": "PostgreSQL",
            "status": "ERROR",
            "message": str(error)
        }

# ==================================================
# BUSINESS RULES RESOURCE
# ==================================================

@mcp.resource("retail://business-rules")
def get_business_rules():

    base_dir = os.path.dirname(
        os.path.abspath(__file__)
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

        return file.read()


# ==================================================
# DATABASE INITIALIZATION
# ==================================================

initialize_database()

seed_sample_data()


# ==================================================
# START SERVER
# ==================================================

if __name__ == "__main__":
    initialize_database()

    mcp.run(
        transport="http",
        host="0.0.0.0",
        port=8000
    )