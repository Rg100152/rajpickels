import re
import sqlite3
from pathlib import Path

from flask import Flask, jsonify, request, send_from_directory

BASE_DIR = Path(__file__).resolve().parent
STATIC_DIR = BASE_DIR / "static"
DB_PATH = BASE_DIR / "rajpickles.db"

PRODUCTS = [
    {"id": "mango", "name": "Mango Achar", "hindi": "आम का आचार", "description": "Sun-dried raw mangoes pickled with mustard oil, fenugreek and hand-ground spices.", "pricePerKg": 650, "emoji": "🥭", "color": "#f5a623", "tag": "Bestseller"},
    {"id": "lemon", "name": "Lemon Achar", "hindi": "नींबू का आचार", "description": "Tangy lemon pickle cured with rock salt, turmeric and ajwain.", "pricePerKg": 550, "emoji": "🍋", "color": "#f8e71c", "tag": "Classic"},
    {"id": "garlic", "name": "Garlic Achar", "hindi": "लहसुन का आचार", "description": "Whole garlic cloves roasted and folded into a fiery red masala base.", "pricePerKg": 750, "emoji": "🧄", "color": "#d0021b", "tag": "Spicy"},
    {"id": "green-chilli", "name": "Green Chilli Achar", "hindi": "हरी मिर्च का आचार", "description": "Fiery green chillies crushed with mustard seeds and lemon juice.", "pricePerKg": 500, "emoji": "🌶️", "color": "#2e7d32", "tag": "Extra Hot"},
    {"id": "carrot", "name": "Carrot Achar", "hindi": "गाजर का आचार", "description": "Crunchy carrot pickle with mustard oil and Punjabi spices.", "pricePerKg": 500, "emoji": "🥕", "color": "#e65100", "tag": "Crunchy"},
    {"id": "mix", "name": "Mixed Achar", "hindi": "मिक्स आचार", "description": "A celebratory medley of mango, lemon, carrot and green chilli.", "pricePerKg": 700, "emoji": "🫙", "color": "#8e44ad", "tag": "Family Pack"},
]

PHONE_RE = re.compile(r"^(?:\+91[-\s]?)?[6-9]\d{9}$")

app = Flask(__name__, static_folder=str(STATIC_DIR), static_url_path="")


def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    with get_db() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS bookings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                customer_name TEXT NOT NULL,
                phone_number TEXT NOT NULL,
                pickle_type TEXT NOT NULL,
                quantity_in_grams INTEGER NOT NULL,
                delivery_address TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'confirmed',
                created_at TEXT NOT NULL DEFAULT (datetime('now'))
            )
            """
        )


def normalize_phone(raw):
    phone = re.sub(r"[\s\-]", "", raw or "")
    if phone.startswith("+91"):
        phone = phone[3:]
    elif phone.startswith("91") and len(phone) == 12:
        phone = phone[2:]
    elif phone.startswith("0") and len(phone) == 11:
        phone = phone[1:]
    return phone


@app.get("/")
def index():
    return send_from_directory(STATIC_DIR, "index.html")


@app.get("/api/health")
def health():
    return jsonify({"status": "ok"})


@app.get("/api/products")
def products():
    return jsonify(PRODUCTS)


@app.post("/api/bookings")
def create_booking():
    data = request.get_json(silent=True) or {}

    name = str(data.get("customerName", "")).strip()
    phone = normalize_phone(str(data.get("phoneNumber", "")))
    pickle_type = str(data.get("pickleType", "")).strip()
    address = str(data.get("deliveryAddress", "")).strip()

    try:
        quantity = int(data.get("quantityInGrams", 0))
    except (TypeError, ValueError):
        quantity = 0

    errors = {}
    if not (2 <= len(name) <= 80):
        errors["customerName"] = "Name must be 2-80 characters."
    if not PHONE_RE.match(phone):
        errors["phoneNumber"] = "Enter a valid Indian mobile number (10 digits, starts 6-9)."
    if pickle_type not in {p["id"] for p in PRODUCTS}:
        errors["pickleType"] = "Please choose a valid pickle type."
    if not (100 <= quantity <= 10000):
        errors["quantityInGrams"] = "Quantity must be between 100 g and 10,000 g."
    if not (10 <= len(address) <= 300):
        errors["deliveryAddress"] = "Address must be 10-300 characters."

    if errors:
        return jsonify({"ok": False, "errors": errors}), 400

    with get_db() as conn:
        cur = conn.execute(
            """
            INSERT INTO bookings (customer_name, phone_number, pickle_type, quantity_in_grams, delivery_address)
            VALUES (?, ?, ?, ?, ?)
            """,
            (name, phone, pickle_type, quantity, address),
        )
        booking_id = cur.lastrowid

    pickle = next(p for p in PRODUCTS if p["id"] == pickle_type)
    amount = round(quantity / 1000 * pickle["pricePerKg"])

    return jsonify({
        "ok": True,
        "booking": {
            "id": booking_id,
            "customerName": name,
            "phoneNumber": phone,
            "pickleType": pickle_type,
            "pickleName": pickle["name"],
            "quantityInGrams": quantity,
            "deliveryAddress": address,
            "estimatedAmount": amount,
        },
    }), 201


@app.get("/api/bookings")
def list_bookings():
    with get_db() as conn:
        rows = conn.execute(
            "SELECT id, customer_name, phone_number, pickle_type, quantity_in_grams, delivery_address, status, created_at FROM bookings ORDER BY id DESC"
        ).fetchall()
    return jsonify([dict(r) for r in rows])


init_db()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
