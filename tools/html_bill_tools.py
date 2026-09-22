from html import escape
from decimal import Decimal


# ============================================================
# MONEY FORMATTER
# ============================================================

def money(value):
    """
    Format a numeric value as Indian Rupees.
    """

    try:
        amount = Decimal(str(value))
        return f"₹{amount:,.2f}"

    except (TypeError, ValueError, ArithmeticError):
        return "₹0.00"


# ============================================================
# HTML ESCAPE
# ============================================================

def safe_text(value):
    """
    Escape user/database content before putting it into HTML.
    """

    if value is None:
        return ""

    return escape(str(value))


# ============================================================
# GENERATE PREMIUM HTML BILL
# ============================================================

def generate_html_bill(order):
    """
    Generate a professional customer-facing HTML invoice.

    IMPORTANT:
    This function intentionally accepts ONLY customer-safe data.

    Never pass:
        cost_price
        order_profit
        lifetime_profit
        remaining_profit
        profit_margin
        supplier_cost
        internal_inventory_valuation
        business_revenue
        business_wide_profit
    """

    order_id = safe_text(
        order.get("order_id")
    )

    order_date = safe_text(
        order.get("order_date")
    )

    customer = order.get(
        "customer",
        {}
    )

    customer_name = safe_text(
        customer.get("name", "Customer")
    )

    customer_email = safe_text(
        customer.get("email", "")
    )

    delivery_status = safe_text(
        order.get(
            "delivery_status",
            "Processing"
        )
    )

    items = order.get(
        "items",
        []
    )

    # --------------------------------------------------------
    # ITEMS
    # --------------------------------------------------------

    item_rows = ""

    for item in items:

        name = safe_text(
            item.get("name", "Item")
        )

        quantity = item.get(
            "quantity",
            0
        )

        selling_price = item.get(
            "selling_price",
            0
        )

        subtotal = item.get(
            "subtotal",
            0
        )

        item_rows += f"""
        <tr>
            <td class="item-name">
                {name}
            </td>

            <td class="center">
                {quantity}
            </td>

            <td class="right">
                {money(selling_price)}
            </td>

            <td class="right total-cell">
                {money(subtotal)}
            </td>
        </tr>
        """

    # --------------------------------------------------------
    # TOTALS
    # --------------------------------------------------------

    subtotal = money(
        order.get(
            "subtotal",
            0
        )
    )

    discount = money(
        order.get(
            "discount",
            0
        )
    )

    final_amount = money(
        order.get(
            "final_amount",
            0
        )
    )

    # --------------------------------------------------------
    # HTML
    # --------------------------------------------------------

    return f"""
<!DOCTYPE html>

<html lang="en">

<head>

<meta charset="UTF-8">

<meta name="viewport"
      content="width=device-width, initial-scale=1.0">

<title>
    RetailOps Invoice #{order_id}
</title>

<style>

html,
body {{
    margin: 0;
    padding: 0;
}}

body {{
    background-color: #f3f4f6;
    font-family:
        Arial,
        Helvetica,
        sans-serif;

    color: #111827;
}}

.container {{
    width: 100%;
    padding: 35px 12px;
}}

.invoice {{
    max-width: 720px;
    margin: 0 auto;

    background: #ffffff;

    border-radius: 18px;

    overflow: hidden;

    box-shadow:
        0 12px 40px
        rgba(0, 0, 0, 0.08);
}}


/* ==========================================================
   HEADER
   ========================================================== */

.header {{
    background:
        linear-gradient(
            135deg,
            #111827,
            #1f2937
        );

    padding: 34px;
    color: #ffffff;
}}

.brand {{
    font-size: 28px;
    font-weight: 800;
    letter-spacing: -0.6px;
}}

.brand-primary {{
    color: #ffffff;
}}

.brand-accent {{
    color: #60a5fa;
}}

.invoice-label {{
    margin-top: 7px;

    font-size: 11px;

    letter-spacing: 2px;

    color: #94a3b8;

    font-weight: 700;
}}

.invoice-meta {{
    margin-top: 28px;
}}

.invoice-number {{
    font-size: 15px;
    font-weight: 600;
}}

.invoice-date {{
    margin-top: 6px;

    font-size: 13px;

    color: #94a3b8;
}}


/* ==========================================================
   CONTENT
   ========================================================== */

.content {{
    padding: 34px;
}}

.greeting {{
    font-size: 23px;

    font-weight: 700;

    color: #111827;
}}

.description {{
    margin-top: 8px;

    color: #6b7280;

    font-size: 14px;

    line-height: 1.6;
}}


/* ==========================================================
   CUSTOMER
   ========================================================== */

.customer-card {{
    margin-top: 26px;

    padding: 19px;

    background: #f8fafc;

    border:
        1px solid
        #e5e7eb;

    border-radius: 13px;
}}

.customer-label {{
    font-size: 10px;

    font-weight: 800;

    letter-spacing: 1.3px;

    color: #64748b;

    text-transform: uppercase;
}}

.customer-name {{
    margin-top: 7px;

    font-size: 16px;

    font-weight: 700;

    color: #111827;
}}

.customer-email {{
    margin-top: 4px;

    font-size: 13px;

    color: #64748b;
}}

.status {{
    display: inline-block;

    margin-top: 12px;

    padding:
        6px 12px;

    border-radius: 999px;

    background: #dcfce7;

    color: #166534;

    font-size: 11px;

    font-weight: 800;
}}


/* ==========================================================
   ORDER SUMMARY
   ========================================================== */

.section-title {{
    margin-top: 32px;

    margin-bottom: 13px;

    font-size: 15px;

    font-weight: 800;

    color: #111827;
}}

table {{
    width: 100%;

    border-collapse:
        collapse;
}}

thead th {{
    padding:
        12px 10px;

    background: #f8fafc;

    border-bottom:
        1px solid
        #e5e7eb;

    color: #64748b;

    font-size: 10px;

    text-transform:
        uppercase;

    letter-spacing: .7px;
}}

tbody td {{
    padding:
        15px 10px;

    border-bottom:
        1px solid
        #eef0f3;

    font-size: 13px;
}}

.item-name {{
    font-weight: 600;

    color: #1f2937;
}}

.center {{
    text-align: center;
}}

.right {{
    text-align: right;
}}

.total-cell {{
    font-weight: 700;
    color: #111827;
}}


/* ==========================================================
   BILL TOTALS
   ========================================================== */

.totals {{
    margin-top: 24px;

    margin-left: auto;

    max-width: 310px;
}}

.total-row {{
    display: flex;

    justify-content:
        space-between;

    padding:
        7px 0;

    font-size: 14px;

    color: #64748b;
}}

.discount {{
    color: #16a34a;
}}

.grand-total {{
    display: flex;

    justify-content:
        space-between;

    margin-top: 8px;

    padding-top: 15px;

    border-top:
        2px solid
        #111827;

    font-size: 20px;

    font-weight: 800;

    color: #111827;
}}


/* ==========================================================
   THANK YOU
   ========================================================== */

.thank-you {{
    margin-top: 32px;

    padding: 22px;

    background: #f8fafc;

    border-radius: 13px;

    text-align: center;
}}

.thank-you-title {{
    font-size: 15px;

    font-weight: 700;

    color: #111827;
}}

.thank-you-text {{
    margin-top: 7px;

    font-size: 13px;

    line-height: 1.6;

    color: #64748b;
}}


/* ==========================================================
   FOOTER
   ========================================================== */

.footer {{
    padding:
        23px 30px;

    background: #111827;

    text-align: center;

    font-size: 11px;

    line-height: 1.6;

    color: #94a3b8;
}}

.footer strong {{
    color: #e5e7eb;
}}


/* ==========================================================
   MOBILE
   ========================================================== */

@media only screen and (max-width: 600px) {{

    .container {{
        padding: 8px;
    }}

    .header {{
        padding: 25px;
    }}

    .content {{
        padding: 24px;
    }}

    .brand {{
        font-size: 24px;
    }}

    thead th,
    tbody td {{
        padding:
            10px 5px;
    }}

    .totals {{
        max-width: 100%;
    }}

}}

</style>

</head>


<body>

<div class="container">

<div class="invoice">


<!-- ======================================================
     HEADER
     ====================================================== -->

<div class="header">

    <div class="brand">

        <span class="brand-primary">
            Retail
        </span>

        <span class="brand-accent">
            Ops
        </span>

    </div>

    <div class="invoice-label">
        DIGITAL PURCHASE INVOICE
    </div>

    <div class="invoice-meta">

        <div class="invoice-number">
            Invoice #{order_id}
        </div>

        <div class="invoice-date">
            {order_date}
        </div>

    </div>

</div>


<!-- ======================================================
     CONTENT
     ====================================================== -->

<div class="content">


    <div class="greeting">
        Thank you, {customer_name}.
    </div>

    <div class="description">

        Your purchase has been successfully
        processed. Please keep this invoice
        for your records.

    </div>


    <!-- CUSTOMER -->

    <div class="customer-card">

        <div class="customer-label">
            Billed To
        </div>

        <div class="customer-name">
            {customer_name}
        </div>

        <div class="customer-email">
            {customer_email}
        </div>

        <div class="status">
            {delivery_status}
        </div>

    </div>


    <!-- ITEMS -->

    <div class="section-title">
        Order Summary
    </div>

    <table>

        <thead>

            <tr>

                <th align="left">
                    Item
                </th>

                <th>
                    Qty
                </th>

                <th align="right">
                    Price
                </th>

                <th align="right">
                    Total
                </th>

            </tr>

        </thead>

        <tbody>

            {item_rows}

        </tbody>

    </table>


    <!-- TOTALS -->

    <div class="totals">

        <div class="total-row">

            <span>
                Subtotal
            </span>

            <span>
                {subtotal}
            </span>

        </div>


        <div class="total-row discount">

            <span>
                Discount
            </span>

            <span>
                - {discount}
            </span>

        </div>


        <div class="grand-total">

            <span>
                Total
            </span>

            <span>
                {final_amount}
            </span>

        </div>

    </div>


    <!-- THANK YOU -->

    <div class="thank-you">

        <div class="thank-you-title">

            Thank you for shopping
            with RetailOps.

        </div>

        <div class="thank-you-text">

            We appreciate your business
            and look forward to serving
            you again.

        </div>

    </div>

</div>


<!-- ======================================================
     FOOTER
     ====================================================== -->

<div class="footer">

    <strong>
        RetailOps
    </strong>

    <br>

    This is an automatically generated
    digital invoice.

    <br>

    Please do not reply to this email.

</div>


</div>

</div>

</body>

</html>
"""