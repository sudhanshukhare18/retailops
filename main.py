import os

from fastmcp import FastMCP

from database import initialize_database

from tools.template_tools import (
    register_template_resources
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

from tools.billing_tools import (
    generate_bill
)

from tools.task_tools import (
    create_task,
    get_pending_tasks,
    approve_task,
    reject_task,
    complete_task,
    check_pending_task_alert
)


# ============================================================
# MCP SERVER
# ============================================================

mcp = FastMCP("RetailOps")


# ============================================================
# COMMUNICATION TEMPLATE RESOURCES
# ============================================================

register_template_resources(mcp)


# ============================================================
# AUTHENTICATION
# ============================================================

@mcp.tool()
def mcp_login(
    username: str,
    password: str
):
    """
    Authenticate a RetailOps user.

    Must be called before protected functionality.
    """

    return login(
        username,
        password
    )


@mcp.tool()
def mcp_logout(
    auth_session_id: str
):
    """
    Logout the authenticated user.
    """

    return logout(
        auth_session_id
    )


@mcp.tool()
def mcp_get_current_user(
    auth_session_id: str
):
    """
    Get the currently authenticated user
    and their role.
    """

    user = get_authenticated_user(
        auth_session_id
    )


    if not user:

        return {
            "success": False,
            "message": "Not authenticated."
        }


    return {
        "success": True,
        "user": user
    }


# ============================================================
# CUSTOMER SESSION
# ============================================================

@mcp.tool()
def mcp_start_customer_session(
    auth_session_id: str,
    customer_name: str,
    mobile: str = None,
    email: str = None
):
    """
    Start a customer shopping session.
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


# ============================================================
# PRODUCT
# ============================================================

@mcp.tool()
def mcp_search_product(
    name: str
):
    """
    Search products by name.
    """

    return search_product(
        name
    )


@mcp.tool()
def mcp_find_product(
    name: str
):
    """
    Find a product using its natural name.
    """

    return find_product_by_name(
        name
    )


@mcp.tool()
def mcp_get_product_price(
    product_id: int
):
    """
    Get the selling price of a product.
    """

    return get_product_price(
        product_id
    )


@mcp.tool()
def mcp_check_stock(
    product_id: int
):
    """
    Check current product stock.
    """

    return check_stock(
        product_id
    )


@mcp.tool()
def mcp_get_all_products():
    """
    Get all products.
    """

    return get_all_product()


# ============================================================
# CART
# ============================================================

@mcp.tool()
def mcp_add_to_cart(
    auth_session_id: str,
    product_name: str,
    quantity: int = 1
):
    """
    Add a product to the current customer's
    cart using the natural product name.
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
    Remove a product from the current cart.
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
    Update cart quantity.
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
    Clear the current cart.
    """

    return clear_cart(
        auth_session_id
    )


# ============================================================
# BILLING
# ============================================================

@mcp.tool()
def mcp_generate_bill(
    auth_session_id: str
):
    """
    Generate a bill for the current customer's cart.
    """

    return generate_bill(
        auth_session_id
    )


# ============================================================
# MANAGER → OWNER TASK MANAGEMENT
# ============================================================

@mcp.tool()
def mcp_create_task(
    auth_session_id: str,
    title: str,
    description: str,
    priority: str = "MEDIUM"
):
    """
    Manager creates a task requiring owner approval.

    Allowed role:
    MANAGER
    """

    return create_task(
        auth_session_id,
        title,
        description,
        priority
    )


@mcp.tool()
def mcp_get_pending_tasks(
    auth_session_id: str
):
    """
    Get tasks currently waiting for owner approval.

    Allowed roles:
    MANAGER
    OWNER
    """

    return get_pending_tasks(
        auth_session_id
    )


@mcp.tool()
def mcp_approve_task(
    auth_session_id: str,
    task_id: int,
    owner_comment: str = ""
):
    """
    Approve a pending manager task.

    Allowed role:
    OWNER
    """

    return approve_task(
        auth_session_id,
        task_id,
        owner_comment
    )


@mcp.tool()
def mcp_reject_task(
    auth_session_id: str,
    task_id: int,
    owner_comment: str
):
    """
    Reject a pending manager task.

    A rejection reason is required.

    Allowed role:
    OWNER
    """

    return reject_task(
        auth_session_id,
        task_id,
        owner_comment
    )


@mcp.tool()
def mcp_complete_task(
    auth_session_id: str,
    task_id: int
):
    """
    Mark an approved task as completed.

    Allowed roles:
    MANAGER
    OWNER
    """

    return complete_task(
        auth_session_id,
        task_id
    )


@mcp.tool()
def mcp_check_pending_task_alert(
    auth_session_id: str
):
    """
    Check whether pending approval tasks
    have exceeded the owner alert threshold.

    The tool only detects the condition.
    Claude's Email Connector handles email delivery.

    Allowed role:
    OWNER
    """

    return check_pending_task_alert(
        auth_session_id
    )


# ============================================================
# HEALTH CHECK
# ============================================================

@mcp.tool()
def mcp_health_check():

    from database import pool

    try:

        with pool.connection() as conn:

            with conn.cursor() as cur:

                cur.execute(
                    "SELECT 1"
                )

                cur.fetchone()


        return {

            "success": True,

            "database":
                "PostgreSQL",

            "status":
                "CONNECTED"
        }


    except Exception as error:

        return {

            "success": False,

            "database":
                "PostgreSQL",

            "status":
                "ERROR",

            "message":
                str(error)
        }


# ============================================================
# BUSINESS RULE RESOURCE
# ============================================================

@mcp.resource(
    "retail://business-rules"
)
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


# ============================================================
# SERVER
# ============================================================

if __name__ == "__main__":

    initialize_database()

    mcp.run(
        transport="http",
        host="0.0.0.0",
        port=8000
    )