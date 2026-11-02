from langchain.tools import tool
from data import users_data
from dotenv import load_dotenv
import logging
from objects import PurchaseItem
from datetime import date,datetime
from typing import List

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s " 
)



# In-memory refund ticket store for demonstration
issued_refund_tickets = set()


def parse_purchase_date(value: str) -> date:
    """Parse purchase dates such as 2026-10-5 or 2026-10-05."""
    return datetime.strptime(value, "%Y-%m-%d").date()


@tool
def get_user_purchase_history(user: str) -> dict:
    """Retrieve the purchase history of a customer using their exact username.

    Use this tool after obtaining the customer's username.
    Returns the customer's purchased products, prices, and purchase dates.
    If the username does not exist, returns status='not_found'.
    """
    logging.info("Retrieving purchase history for user: %s", user)

    if not user or user not in users_data:
        return {
            "status": "not_found",
            "message": "No customer found with the provided username."
        }

    return {
        "status": "success",
        "username": user,
        "purchase_history": users_data[user]
    }


@tool
def get_today_date() -> str:
    """Return the current date in YYYY-MM-DD format.

    Use this tool when a valid customer and purchased item have
    been identified and before evaluating refund eligibility.
    """
    logging.info("Retrieving today's date")

    return date.today().isoformat()


@tool
def calculate_right_refund(
    user: str,
    items: List[PurchaseItem]
) -> dict:
    """Calculate the exact refund amount for specific purchased items.

    Arguments:
    - user: Exact customer username.
    - items: List of products the customer wants to refund.

    Only calculate refunds for products that exist in the customer's
    purchase history and were purchased within the last 30 days.

    Reject unknown products, future purchase dates, and expired purchases.
    Never estimate or invent prices.
    """
    logging.info("Calculating refund for user: %s", user)

    if not user or user not in users_data:
        return {
            "status": "not_found",
            "message": "Customer not found."
        }

    if not items:
        return {
            "status": "error",
            "message": "No refund items were provided."
        }

    today = date.today()
    total_refund = 0
    approved_items = []

    for item in items:
        product = users_data[user].get(item.name)

        if product is None:
            return {
                "status": "error",
                "message": f"Product '{item.name}' was not purchased by this customer."
            }

        purchase_date = parse_purchase_date(product["date"])
        days_since_purchase = (today - purchase_date).days

        if days_since_purchase < 0:
            return {
                "status": "ineligible",
                "message": f"Product '{item.name}' has an invalid future purchase date."
            }

        if days_since_purchase > 30:
            return {
                "status": "ineligible",
                "message": f"Product '{item.name}' was purchased more than 30 days ago."
            }

        price = product["price"]
        total_refund += price

        approved_items.append({
            "name": item.name,
            "price": price,
            "purchase_date": product["date"]
        })

    return {
        "status": "success",
        "username": user,
        "approved_items": approved_items,
        "refund_amount": total_refund,
        "currency": "USD"
    }


@tool
def issue_refund_ticket(
    user: str,
    items: List[PurchaseItem],
    refund_amount: int
) -> dict:
    """Issue a refund ticket for eligible purchased items.

    Arguments:
    - user: Exact customer username.
    - items: Exact products approved for refund.
    - refund_amount: Amount returned by calculate_right_refund.

    Recalculate and verify the refund amount before issuing the ticket.
    Reject invalid products, ineligible purchases, and mismatched amounts.
    Do not issue duplicate tickets for the same user and products.
    """
    logging.info("Issuing refund ticket for user: %s", user)

    # Independently verify the refund before processing.
    verification = calculate_right_refund.invoke({
        "user": user,
        "items": [item.model_dump() for item in items]
    })

    if verification["status"] != "success":
        return {
            "status": "rejected",
            "message": "Refund verification failed.",
            "details": verification
        }

    actual_amount = verification["refund_amount"]

    if refund_amount != actual_amount:
        return {
            "status": "rejected",
            "message": "The provided refund amount does not match the verified amount."
        }

    item_names = tuple(sorted(item.name for item in items))
    ticket_key = (user, item_names)

    if ticket_key in issued_refund_tickets:
        return {
            "status": "duplicate",
            "message": "A refund ticket already exists for these items."
        }

    issued_refund_tickets.add(ticket_key)

    ticket_id = f"REF-{len(issued_refund_tickets):05d}"

    logging.info(
        "Refund ticket %s issued for user %s: %s",
        ticket_id, user, actual_amount
    )

    return {
        "status": "success",
        "ticket_id": ticket_id,
        "username": user,
        "items": list(item_names),
        "refund_amount": actual_amount,
        "currency": "USD",
        "message": "Refund ticket successfully issued."
    }