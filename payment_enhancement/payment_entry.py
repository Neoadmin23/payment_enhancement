# import frappe

# def allow_flexible_payment_entry(doc, method):
#     """
#     Payment Entry Hook:
#     - Works for Employee, Supplier, Customer
#     - Uses the Paid From / Paid To already set in the document
#     - Does not throw errors for missing party accounts
#     - Syncs amounts automatically
#     """
#     # Only handle Employee, Supplier, Customer
#     if doc.party_type not in ("Employee", "Supplier", "Customer"):
#         return

#     # Ensure Payment Type is valid
#     if doc.payment_type not in ("Pay", "Receive"):
#         frappe.throw("Payment Type must be either 'Pay' or 'Receive'.")

#     # Only assign Paid From / Paid To if they are already empty
#     if doc.payment_type == "Receive":
#         if not doc.paid_from:
#             doc.paid_from = None  # keep None if not set
#         if not doc.paid_to:
#             doc.paid_to = None
#     else:  # Pay
#         if not doc.paid_from:
#             doc.paid_from = None
#         if not doc.paid_to:
#             doc.paid_to = None

#     # Sync amounts safely
#     if doc.payment_type == "Receive":
#         doc.received_amount = doc.received_amount or doc.paid_amount or 0
#     else:
#         doc.paid_amount = doc.paid_amount or doc.received_amount or 0

#     # Recompute internal fields safely
#     try:
#         if hasattr(doc, "set_missing_values"):
#             doc.set_missing_values()
#         if hasattr(doc, "set_exchange_rate"):
#             doc.set_exchange_rate()
#         if hasattr(doc, "set_amounts"):
#             doc.set_amounts()
#         if hasattr(doc, "set_difference_amount"):
#             doc.set_difference_amount()
#     except Exception:
#         pass


import frappe

def allow_flexible_payment_entry(doc, method):
    """
    Flexible Payment Entry Hook for ERPNext:
    - Works for Employee, Supplier, Customer
    - Prevents 'Party Type and Party can only be set for Receivable / Payable account' errors
    - Auto-syncs Paid/Received amounts
    """

    if doc.party_type not in ("Employee", "Supplier", "Customer", None):
        return

    if doc.payment_type not in ("Pay", "Receive"):
        frappe.throw("Payment Type must be either 'Pay' or 'Receive'.")

    # Helper: check if account is Cash or Bank
    def is_cash_or_bank(account):
        if not account:
            return False
        account_type = frappe.db.get_value("Account", account, "account_type")
        return account_type in ("Cash", "Bank")

    # --- Handle Receive Type ---
    if doc.payment_type == "Receive":
        if is_cash_or_bank(doc.paid_to):
            doc.party_type = None
            doc.party = None
        doc.received_amount = doc.received_amount or doc.paid_amount or 0
        doc.paid_amount = doc.paid_amount or doc.received_amount or 0

    # --- Handle Pay Type ---
    elif doc.payment_type == "Pay":
        if is_cash_or_bank(doc.paid_from):
            doc.party_type = None
            doc.party = None
        doc.paid_amount = doc.paid_amount or doc.received_amount or 0
        doc.received_amount = doc.received_amount or doc.paid_amount or 0

    # --- Safely trigger ERPNext internal recalculations ---
    for fn in (
        "set_missing_values",
        "set_exchange_rate",
        "set_amounts",
        "set_difference_amount",
    ):
        if hasattr(doc, fn):
            try:
                getattr(doc, fn)()
            except Exception:
                pass
