import base64
import json
from google.cloud import firestore

def order_notifier(event, context):
    #encode pub/sub message
    data_b64 = event.get("data", "")
    if not data_b64:
        print("No data in message")
        return

    decoded = base64.b64decode(data_b64).decode("utf-8")
    payload = json.loads(decoded)

    print("Order created event:", payload)

    db = firestore.Client()
    db.collection("order_notifications").add({
        "order_id": payload.get("order_id"),
        "user_email": payload.get("user_email"),
        "total": payload.get("total"),
        "status": "received"
    })