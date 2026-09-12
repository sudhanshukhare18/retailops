import os

from fastmcp import FastMCP

from database import initialize_database

from tools.template_tools import (
    register_template_resources,
    register_template
)

from tools.auth_tools import (
    login,
    logout,
    get_authenticated_user
)

from tools.session_tools import (
    start_customer_session,
    get_current_customer_session,
    end_customer_session
)

from tools.cart_tools import (
    add_to_cart,
    remove_from_cart,
    update_cart_quantity,
    view_cart,
    clear_cart
)

from tools.product_tools import (
    search_product,
    find_product_by_name,
    get_product_price,
    check_stock,
    get_all_product
)

from tools.billing_tools import generate_bill


mcp = FastMCP("RetailOps")


# ==========================================
# COMMUNICATION TEMPLATES
# ==========================================

register_template_resources(mcp)
register_template(mcp)


# ==========================================
# AUTHENTICATION
# ==========================================

@mcp.tool()
def mcp_login(
    username: str,
    password: str
):
    """
    Authenticate a RetailOps user.

    Must be called before using protected functionality.
    """
    return login(username, password)


@mcp.tool()
def mcp_logout(
    auth_session_id: str
):
    """
    Logout the currently authenticated user.
    """
    return logout(auth_session_id)


@mcp.tool()
def mcp_get_current_user(
    auth_session_id: str
):
    """
    Get the currently authenticated user.
    """

    user = get_authenticated_user(auth_session_id)

    if not user:
        return {
            "success": False,
            "message": "Not authenticated."
        }

    return {
        "success": True,
        "user": user
    }


# ==========================================
# CUSTOMER SESSION
# ==========================================

@mcp.tool()
def mcp_start_customer_session(
    auth_session_id: str,
    customer_name: str,
    mobile: str = None,
    email: str = None
):
    """
    Start a customer session.

    If the customer already exists, mobile identifies them.
    For a new customer, mobile and email are collected.
    """

    return start_customer_session(
        auth_session_id,
        customer_name,
        mobile,
        email
    )


@mcp.tool()
def mcp_get_current_customer(
    auth_session_id: str
):
    """
    Get the customer currently associated
    with the authenticated salesperson session.
    """

    return get_current_customer_session(
        auth_session_id
    )


@mcp.tool()
def mcp_end_customer_session(
    auth_session_id: str
):
    """
    End the current customer session.
    """

    return end_customer_session(
        auth_session_id
    )


# ==========================================
# PRODUCT
# ==========================================

@mcp.tool()
def mcp_search_product(
    name: str
):
    """
    Search products by name.
    """
    return search_product(name)


@mcp.tool()
def mcp_find_product(
    name: str
):
    """
    Find a product by its natural name.
    """
    return find_product_by_name(name)


@mcp.tool()
def mcp_get_product_price(
    product_id: int
):
    """
    Get the selling price of a product.
    """
    return get_product_price(product_id)


@mcp.tool()
def mcp_check_stock(
    product_id: int
):
    """
    Check current stock of a product.
    """
    return check_stock(product_id)


@mcp.tool()
def mcp_get_all_products():
    """
    Get all products.
    """
    return get_all_product()


# ==========================================
# CART
# ==========================================

@mcp.tool()
def mcp_add_to_cart(
    auth_session_id: str,
    product_name: str,
    quantity: int = 1
):
    """
    Add a product to the current customer's cart
    using the product name.
    """

    return add_to_cart(
        auth_session_id,
        product_name,
        quantity
    )


@mcp.tool()
def mcp_remove_from_cart(
    auth_session_id: str,
    product_id: int
):
    """
    Remove a product from the current customer's cart.
    """

    return remove_from_cart(
        auth_session_id,
        product_id
    )


@mcp.tool()
def mcp_update_cart_quantity(
    auth_session_id: str,
    product_id: int,
    quantity: int
):
    """
    Update the quantity of a product in the cart.
    """

    return update_cart_quantity(
        auth_session_id,
        product_id,
        quantity
    )


@mcp.tool()
def mcp_view_cart(
    auth_session_id: str
):
    """
    View the current customer's cart.
    """

    return view_cart(
        auth_session_id
    )


@mcp.tool()
def mcp_clear_cart(
    auth_session_id: str
):
    """
    Clear the current customer's cart.
    """

    return clear_cart(
        auth_session_id
    )


# ==========================================
# BILLING
# ==========================================

@mcp.tool()
def mcp_generate_bill(
    auth_session_id: str
):
    """
    Generate the bill for the current customer's cart.
    """

    return generate_bill(
        auth_session_id
    )


# ==========================================
# HEALTH
# ==========================================

@mcp.tool()
def mcp_health_check():

    from database import pool

    try:

        with pool.connection() as conn:

            with conn.cursor() as cur:

                cur.execute("SELECT 1")
                cur.fetchone()

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


# ==========================================
# BUSINESS RULE RESOURCE
# ==========================================

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


# ==========================================
# SERVER
# ==========================================

if __name__ == "__main__":

    initialize_database()

    mcp.run(
        transport="http",
        host="0.0.0.0",
        port=8000
    )