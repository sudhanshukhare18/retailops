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
# GOOGLE DRIVE TEMPLATE CONFIGURATION
# ============================================================

GOOGLE_DRIVE_FOLDER = "RetailOps Templates"

GOOGLE_DRIVE_DESCRIPTION = (
    "Google Drive folder containing approved RetailOps "
    "communication and document templates."
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
    # Complete communication policy + template metadata
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
    # Google Drive document template specification
    # ========================================================

    @mcp.resource(
        "templates://documents/bill"
    )
    def bill_document_template():

        bill_template = {

            "success": True,

            "name": "Customer Bill Document",

            "description": (
                "Approved DOCX template used to create "
                "the customer's final bill."
            ),

            "audience": "customer",

            "storage": {

                "provider": "Google Drive",

                "folder": GOOGLE_DRIVE_FOLDER,

                "file_name": "bill_template.docx",

                "description": GOOGLE_DRIVE_DESCRIPTION

            },

            "retrieval_instruction": (
                "Retrieve the approved bill_template.docx "
                "from the RetailOps Templates folder in "
                "Google Drive. Do not use an alternative "
                "template."
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
    # Get approved communication template
    # ========================================================

    @mcp.tool()
    def get_communication_template(
        template_name: str
    ):

        """
        Retrieve an approved RetailOps communication
        template definition.

        The actual document files are stored in the
        RetailOps Templates folder in Google Drive.

        Customer-facing communication must use an
        approved RetailOps template.
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

            "storage": {

                "provider": "Google Drive",

                "folder": GOOGLE_DRIVE_FOLDER

            },

            "instruction": (
                "Use the approved RetailOps template. "
                "If a physical document template is required, "
                "retrieve it from the RetailOps Templates "
                "folder in Google Drive using the connected "
                "Google Drive integration. Do not create or "
                "substitute an unapproved template."
            )

        }


    # ========================================================
    # TOOL 2
    # Explicit customer bill template
    # ========================================================

    @mcp.tool()
    def get_customer_bill_template():

        """
        Retrieve the approved customer bill communication
        template and Google Drive document information.

        The actual bill_template.docx is stored in Google
        Drive and should be retrieved by Claude using its
        connected Google Drive integration.
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

            "document_template": {

                "provider": "Google Drive",

                "folder": GOOGLE_DRIVE_FOLDER,

                "file_name": "bill_template.docx"

            },

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

            ],

            "instruction": (
                "Use this approved customer bill template "
                "for customer communication. Retrieve "
                "bill_template.docx from the RetailOps Templates "
                "folder in Google Drive. Populate only the "
                "allowed customer-facing fields. Never include "
                "cost price, profit, margins, supplier cost, "
                "or other internal business information."
            )

        }