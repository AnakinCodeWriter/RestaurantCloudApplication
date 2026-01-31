from google.cloud import firestore

def get_client():
    return firestore.Client()

def list_menu_items():
    db = get_client()
    docs = db.collection("menu_items").stream()
    items = []
    for doc in docs:
        data = doc.to_dict()
        data["id"] = doc.id
        items.append(data)
    return items

def add_menu_item(name: str, price: float, category: str = "main", tags=None):
    if tags is None:
        tags = []
    db = get_client()
    db.collection("menu_items").add({
        "name": name,
        "price": float(price),
        "category": category,
        "tags": tags
    })