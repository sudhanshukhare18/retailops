import json
import os

from fastmcp import FastMCP


# ============================================================
# PATH
# ============================================================

BASE_DIR = os.path.dirname(
    os.path.dirname(
        os.path.abspath(__file__)
    )
)

TEMPLATE_FILE = os.path.join(
    BASE_DIR,
    "resources",
    "communication_templates.json"
)


# ============================================================
# LOAD JSON
# ============================================================

def load_communication_templates():
    with open(
        TEMPLATE_FILE,
        "r",
        encoding="utf-8"
    ) as file:
        return json.load(file)


# ============================================================
# INTERNAL TEMPLATE LOADER
# ============================================================

def get_template(template_name: str):

    data = load_communication_templates()

    templates = data.get(
        "templates",
        {}
    )

    template = templates.get(
        template_name
    )

    if not template:
        return None

    return template


# ============================================================
# REGISTER MCP RESOURCES + TOOLS
# ============================================================

def register_template_resources(mcp: FastMCP):

    # ========================================================
    # RESOURCE 1
    # Complete communication policy + templates
    # ========================================================

    @mcp.resource(
        "templates://communication"
    )
    def communication_templates():

        templates = load_communication_templates()

        return json.dumps(
            templates,
            indent=2,
            ensure_ascii=False
        )


    # ========================================================
    # RESOURCE 2
    # Communication policy only
    # ========================================================

    @mcp.resource(
        "policies://communication"
    )
    def communication_policy():

        templates = load_communication_templates()

        policy = templates.get(
            "communication_policy",
            {}
        )

        return json.dumps(
            policy,
            indent=2,
            ensure_ascii=False
        )


    # ========================================================
    # RESOURCE 3
    # Individual communication template
    # ========================================================

    @mcp.resource(
        "templates://communication/{template_name}"
    )
    def communication_template(
        template_name: str
    ):

        template = get_template(
            template_name
        )

        if not template:

            return json.dumps({
                "success": False,
                "message": (
                    f"Template '{template_name}' "
                    "does not exist."
                )
            })

        return json.dumps(
            template,
            indent=2,
            ensure_ascii=False
        )


    # ========================================================
    # RESOURCE 4
    # Bill document specification
    # ========================================================

    @mcp.resource(
        "templates://documents/bill"
    )
    def bill_document_template():

        bill_template = {
            "name": "Customer Bill Document",

            "description": (
                "DOCX template used to create "
                "the customer's final bill."
            ),

            "audience": "customer",

            "file": (
                "resources/documents/"
                "bill_template.docx"
            ),

            "allowed_fields": [
                "customer_name",
                "order_id",
                "order_date",
                "items",
                "subtotal",
                "discount",
                "final_amount",
                "delivery_status"
            ],

            "forbidden_fields": [
                "cost_price",
                "order_profit",
                "lifetime_profit",
                "profit_margin",
                "remaining_profit",
                "supplier_cost",
                "internal_inventory_valuation",
                "employee_performance",
                "business_revenue",
                "business_wide_profit"
            ]
        }

        return json.dumps(
            bill_template,
            indent=2,
            ensure_ascii=False
        )


    # ========================================================
    # TOOL 1
    # Get any approved communication template
    # ========================================================

    @mcp.tool()
    def get_communication_template(
        template_name: str
    ):

        """
        Retrieve an approved RetailOps communication template.

        IMPORTANT:
        Customer-facing communication must use an approved
        RetailOps template. Do not invent a new template.
        """

        template = get_template(
            template_name
        )

        if not template:

            return {
                "success": False,
                "message": (
                    f"Approved template "
                    f"'{template_name}' was not found."
                )
            }

        return {
            "success": True,
            "template_name": template_name,
            "template": template,
            "instruction": (
                "Use this approved template exactly. "
                "Do not create alternative customer-facing wording."
            )
        }


    # ========================================================
    # TOOL 2
    # Explicit customer bill template
    # ========================================================

    @mcp.tool()
    def get_customer_bill_template():

        """
        Retrieve the approved customer bill email template.

        This is the ONLY approved template for sending a
        customer's bill by email.
        """

        template = get_template(
            "customer_bill"
        )

        if not template:

            return {
                "success": False,
                "message": (
                    "The approved customer_bill "
                    "template does not exist."
                )
            }

        return {
            "success": True,
            "template_name": "customer_bill",
            "audience": "customer",
            "template": template,
            "instruction": (
                "Use this template exactly for customer bill "
                "emails. Do not generate a different email body."
            )
        }