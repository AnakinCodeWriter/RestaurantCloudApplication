import base64
import json
from datetime import datetime, timezone
from google.cloud import firestore

def order_notifier(request):
    envelope = request.get_json(silent=True) or {}
    message = envelope.get("message", {})
    data_b64 = message.get("data", "")

    if not data_b64:
        print("No Pub/Sub message data")
        return ("No data", 200)

    decoded = base64.b64decode(data_b64).decode("utf-8")
    payload = json.loads(decoded)

    order_id = payload.get("order_id")
    user_email = payload.get("user_email")
    total = payload.get("total")

    #building the receipt
    receipt_text = (
        f"Receipt\n"
        f"Order ID: {order_id}\n"
        f"Customer: {user_email}\n"
        f"Total: £{total}\n"
        f"Timestamp (UTC): {datetime.now(timezone.utc).isoformat()}\n"
        f"Thank you for your order!"
    )

    print("=== RECEIPT (demo) ===")
    print(receipt_text)
    print("======================")

    db = firestore.Client()

    db.collection("order_notifications").add({
        "order_id": order_id,
        "user_email": user_email,
        "total": total,
        "status": "received",
        "created_at": firestore.SERVER_TIMESTAMP
    })

    db.collection("receipts").add({
        "order_id": order_id,
        "user_email": user_email,
        "total": total,
        "receipt_text": receipt_text,
        "created_at": firestore.SERVER_TIMESTAMP
    })

    return ("OK", 200)