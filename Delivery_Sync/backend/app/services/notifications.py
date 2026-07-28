"""
Sends a customer notification when a delivery's status changes, via
whichever contact channel(s) are actually on file for that delivery.
Neither, either, or both of email/SMS may fire — nothing is required.

Kept as its own thin module (rather than calling email.py/sms.py
directly from the route/conflict-resolver code) so the call site only
needs to know "notify about this status change" — not which channels
exist or how each one is contacted.

A notification failure (bad SMTP config, Twilio error, etc.) is caught
and logged here rather than allowed to propagate — sending a customer
notification is a nice-to-have side effect of a status update, and must
never be the reason the actual status update itself fails.
"""

import os

from app.services.email import send_status_notification_email
from app.services.sms import send_status_notification_sms

FRONTEND_URL = os.environ.get("FRONTEND_URL", "http://localhost:3000")

STATUS_LABELS = {
    "picked_up": "Picked Up",
    "out_for_delivery": "Out for Delivery",
    "delivered": "Delivered",
    "failed_attempt": "Delivery Attempt Failed",
}


def notify_customer_of_status_change(
    delivery_id: str,
    order_id: str,
    new_status: str,
    customer_email: str | None,
    customer_phone: str | None,
) -> None:
    status_label = STATUS_LABELS.get(new_status, new_status)
    tracking_link = f"{FRONTEND_URL}/?track={delivery_id}"

    if customer_email:
        try:
            send_status_notification_email(customer_email, order_id, status_label, tracking_link)
        except Exception as error:  # noqa: BLE001
            print(f"Email notification failed for {order_id}: {error}")

    if customer_phone:
        try:
            send_status_notification_sms(customer_phone, order_id, status_label, tracking_link)
        except Exception as error:  # noqa: BLE001
            print(f"SMS notification failed for {order_id}: {error}")
