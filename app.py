import os
import json
import random
import re
from datetime import datetime, timedelta
from functools import wraps
from flask import (
    Flask, render_template, request, redirect, url_for,
    session, flash, jsonify, send_from_directory
)
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "motoqr-dev-secret-change-in-prod")
app.config["MAX_CONTENT_LENGTH"] = 8 * 1024 * 1024

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")
IMAGE_DIR = os.path.join(BASE_DIR, "image")
USERS_FILE = os.path.join(DATA_DIR, "users.json")
MOTORCYCLES_FILE = os.path.join(DATA_DIR, "motorcycles.json")
RENTALS_FILE = os.path.join(DATA_DIR, "rentals.json")
RETURNS_FILE = os.path.join(DATA_DIR, "return_requests.json")
NOTIFICATIONS_FILE = os.path.join(DATA_DIR, "notifications.json")
SUPPORT_FILE = os.path.join(DATA_DIR, "support_messages.json")
CAPTURED_IDS_DIR = os.path.join(BASE_DIR, "captured_ids")

LATE_FEE_PER_DAY = 100
GPS_CENTER_LAT = 14.5995
GPS_CENTER_LNG = 120.9842
gps_positions = {}
LOGIN_MAX_ATTEMPTS = 5
LOGIN_LOCK_MINUTES = 5
_login_attempts = {}


def ensure_dirs():
    os.makedirs(DATA_DIR, exist_ok=True)
    os.makedirs(CAPTURED_IDS_DIR, exist_ok=True)


def load_json(path, default):
    try:
        if os.path.exists(path):
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
                if isinstance(data, type(default)):
                    return data
    except Exception:
        pass
    return default


def save_json(path, data):
    ensure_dirs()
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def default_motorcycles():
    names = [
        ("M001", "Honda Click 125i", 500), ("M002", "Yamaha Mio Sporty", 450),
        ("M003", "Honda Beat", 400), ("M004", "Yamaha Aerox", 700),
        ("M005", "Honda ADV 160", 800), ("M006", "Yamaha NMAX", 750),
        ("M007", "Honda PCX 160", 750), ("M008", "Suzuki Raider 150", 600),
        ("M009", "Honda XRM 125", 550), ("M010", "Yamaha Sniper 155", 650),
        ("M011", "Honda CBR150R", 900), ("M012", "Yamaha R15", 950),
        ("M013", "Kawasaki Ninja 400", 1200), ("M014", "Yamaha MT-15", 850),
        ("M015", "Honda CB150R", 800), ("M016", "Suzuki Burgman Street", 550),
        ("M017", "Yamaha Fazzio", 500), ("M018", "Honda Airblade 160", 700),
        ("M019", "Kawasaki Rouser NS160", 700), ("M020", "Suzuki Raider R150", 650),
    ]
    return [{"id": mid, "name": name, "rate": rate, "status": "Available",
             "image": f"image/{mid}.jpg"} for mid, name, rate in names]


def get_users():
    users = load_json(USERS_FILE, [])
    if not any(u.get("username") == "admin" for u in users):
        users.insert(0, {"username": "admin", "password": "1234", "role": "Admin"})
        save_json(USERS_FILE, users)
    return users


def get_motorcycles():
    bikes = load_json(MOTORCYCLES_FILE, [])
    if not bikes:
        bikes = default_motorcycles()
        save_json(MOTORCYCLES_FILE, bikes)
    return bikes


def get_rentals():
    return load_json(RENTALS_FILE, [])


def get_returns():
    return load_json(RETURNS_FILE, [])


def get_notifications():
    return load_json(NOTIFICATIONS_FILE, [])


def get_support_messages():
    return load_json(SUPPORT_FILE, [])


def save_users(u):
    save_json(USERS_FILE, u)


def save_motorcycles(b):
    save_json(MOTORCYCLES_FILE, b)


def save_rentals(r):
    save_json(RENTALS_FILE, r)


def save_returns(r):
    save_json(RETURNS_FILE, r)


def save_notifications(n):
    save_json(NOTIFICATIONS_FILE, n)


def save_support_messages(m):
    save_json(SUPPORT_FILE, m)


def normalize_phone(value):
    return re.sub(r"\D", "", value or "")


def notify(username, title, message, ntype="info"):
    notes = get_notifications()
    notes.append({
        "id": f"N{datetime.now().strftime('%Y%m%d%H%M%S')}{random.randint(100, 999)}",
        "username": username, "title": title, "message": message,
        "type": ntype, "read": False,
        "date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    })
    save_notifications(notes)


def notify_admins(title, message, ntype="info"):
    for u in get_users():
        if u.get("role") == "Admin":
            notify(u["username"], title, message, ntype)


def unread_count(username):
    return sum(1 for n in get_notifications()
               if n.get("username") == username and not n.get("read"))


def current_user():
    return {"username": session.get("username"), "role": session.get("role")}


def login_required(f):
    @wraps(f)
    def wrapped(*args, **kwargs):
        if not session.get("username"):
            flash("Please log in first.", "warning")
            return redirect(url_for("login"))
        return f(*args, **kwargs)
    return wrapped


def admin_required(f):
    @wraps(f)
    def wrapped(*args, **kwargs):
        if not session.get("username"):
            return redirect(url_for("login"))
        if session.get("role") != "Admin":
            flash("Admin access only.", "danger")
            return redirect(url_for("client_home"))
        return f(*args, **kwargs)
    return wrapped


def _login_status(username):
    key = (username or "").strip().lower()
    rec = _login_attempts.get(key)
    if not rec:
        return False, 0, LOGIN_MAX_ATTEMPTS
    locked_until = rec.get("locked_until")
    if locked_until and datetime.now() < locked_until:
        remaining = int((locked_until - datetime.now()).total_seconds())
        return True, max(1, remaining), 0
    if locked_until and datetime.now() >= locked_until:
        _login_attempts.pop(key, None)
        return False, 0, LOGIN_MAX_ATTEMPTS
    return False, 0, max(0, LOGIN_MAX_ATTEMPTS - rec.get("count", 0))


def _record_login_failure(username):
    key = (username or "").strip().lower()
    if not key:
        return LOGIN_MAX_ATTEMPTS
    rec = _login_attempts.get(key) or {"count": 0, "locked_until": None}
    if rec.get("locked_until") and datetime.now() >= rec["locked_until"]:
        rec = {"count": 0, "locked_until": None}
    rec["count"] = rec.get("count", 0) + 1
    if rec["count"] >= LOGIN_MAX_ATTEMPTS:
        rec["locked_until"] = datetime.now() + timedelta(minutes=LOGIN_LOCK_MINUTES)
        rec["count"] = LOGIN_MAX_ATTEMPTS
    _login_attempts[key] = rec
    return max(0, LOGIN_MAX_ATTEMPTS - rec["count"])


def _clear_login_failures(username):
    _login_attempts.pop((username or "").strip().lower(), None)


def client_active_rentals(username):
    return [r for r in get_rentals()
            if r.get("username") == username
            and r.get("status") in ("Rented", "Overdue", "Pending Confirmation")]


def client_contact(username):
    rentals = sorted(
        [r for r in get_rentals() if r.get("username") == username and r.get("contact")],
        key=lambda r: r.get("date", ""), reverse=True,
    )
    return rentals[0]["contact"] if rentals else ""


def open_support_count():
    return sum(1 for m in get_support_messages() if m.get("status") == "Open")


def parse_rental_dt(date_str):
    for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d"):
        try:
            return datetime.strptime(date_str, fmt)
        except Exception:
            continue
    return None


def overdue_days(rental):
    start = parse_rental_dt(rental.get("date", ""))
    if not start:
        return 0
    try:
        days = int(rental.get("days", 0))
    except Exception:
        days = 0
    due = start + timedelta(days=days)
    now = datetime.now()
    if now <= due:
        return 0
    delta = now - due
    return max(1, delta.days + (1 if delta.seconds else 0))


def check_overdue():
    rentals = get_rentals()
    changed = False
    for rental in rentals:
        if rental.get("status") not in ("Rented", "Overdue"):
            continue
        od = overdue_days(rental)
        if od <= 0:
            continue
        fee = od * LATE_FEE_PER_DAY
        if rental.get("status") != "Overdue" or rental.get("late_fee") != fee:
            rental["status"] = "Overdue"
            rental["late_fee"] = fee
            rental["overdue_days"] = od
            changed = True
        if not rental.get("overdue_notified"):
            notify(rental["username"], "Rental Overdue — Late Fee Applied",
                   f"Your rental of {rental['motorcycle']} is overdue by {od} day(s).\n"
                   f"Late fee: PHP {LATE_FEE_PER_DAY}/day. Current fee: PHP {fee}.",
                   ntype="danger")
            rental["overdue_notified"] = True
            changed = True
    if changed:
        save_rentals(rentals)


def start_gps(motorcycle_id, name, username):
    gps_positions[motorcycle_id] = {
        "lat": GPS_CENTER_LAT + random.uniform(-0.03, 0.03),
        "lng": GPS_CENTER_LNG + random.uniform(-0.03, 0.03),
        "name": name, "username": username,
        "updated": datetime.now().strftime("%H:%M:%S"),
    }


def stop_gps(motorcycle_id):
    gps_positions.pop(motorcycle_id, None)


def tick_gps():
    for pos in gps_positions.values():
        pos["lat"] += random.uniform(-0.0015, 0.0015)
        pos["lng"] += random.uniform(-0.0015, 0.0015)
        pos["lat"] = max(14.45, min(14.75, pos["lat"]))
        pos["lng"] = max(120.90, min(121.10, pos["lng"]))
        pos["updated"] = datetime.now().strftime("%H:%M:%S")


def init_gps_from_rentals():
    for r in get_rentals():
        if r.get("status") in ("Rented", "Overdue"):
            mid = r.get("motorcycle_id") or r.get("motorcycle")
            if mid and mid not in gps_positions:
                start_gps(mid, r.get("motorcycle", mid), r.get("username", ""))


@app.route("/image/<path:filename>")
def serve_image(filename):
    return send_from_directory(IMAGE_DIR, filename)


@app.route("/uploads/<path:filename>")
@login_required
def serve_upload(filename):
    return send_from_directory(CAPTURED_IDS_DIR, filename)


@app.route("/")
def index():
    if session.get("username"):
        if session.get("role") == "Admin":
            return redirect(url_for("admin_home"))
        return redirect(url_for("client_home"))
    return redirect(url_for("login"))


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        locked, remaining, _left = _login_status(username)
        if locked:
            mins, secs = remaining // 60, remaining % 60
            flash(f"Account locked. Try again in {mins}m {secs:02d}s.", "danger")
            return render_template("login.html", lock_remaining=remaining)
        matched = None
        for user in get_users():
            if user["username"] == username and user["password"] == password:
                matched = user
                break
        if matched:
            _clear_login_failures(username)
            session["username"] = matched["username"]
            session["role"] = matched["role"]
            flash(f"Welcome, {username}!", "success")
            if matched["role"] == "Admin":
                return redirect(url_for("admin_home"))
            return redirect(url_for("client_home"))
        left = _record_login_failure(username)
        locked, remaining, _ = _login_status(username)
        if locked:
            flash(f"Too many failed attempts. Locked for {LOGIN_LOCK_MINUTES} minutes.", "danger")
        elif left > 0:
            flash(f"Incorrect credentials. {left} attempt(s) left.", "danger")
        else:
            flash("Incorrect username or password.", "danger")
    return render_template("login.html")


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        if not username or not password:
            flash("Enter username and password.", "warning")
            return render_template("register.html")
        users = get_users()
        if any(u["username"] == username for u in users):
            flash("Username already exists.", "danger")
            return render_template("register.html")
        users.append({"username": username, "password": password, "role": "Client"})
        save_users(users)
        flash("Account created. Please log in.", "success")
        return redirect(url_for("login"))
    return render_template("register.html")


@app.route("/logout")
def logout():
    session.clear()
    flash("Logged out.", "info")
    return redirect(url_for("login"))


@app.route("/notifications")
@login_required
def notifications():
    items = [n for n in get_notifications() if n.get("username") == session["username"]]
    items.sort(key=lambda n: n.get("date", ""), reverse=True)
    notes = get_notifications()
    for n in notes:
        if n.get("username") == session["username"]:
            n["read"] = True
    save_notifications(notes)
    return render_template("notifications.html", user=current_user(), items=items, unread=0)


@app.route("/client")
@login_required
def client_home():
    if session.get("role") == "Admin":
        return redirect(url_for("admin_home"))
    check_overdue()
    bikes = get_motorcycles()
    return render_template(
        "client_home.html", user=current_user(), bikes=bikes,
        available=sum(1 for b in bikes if b["status"] == "Available"),
        reserved=sum(1 for b in bikes if b["status"] == "Reserved"),
        rented=sum(1 for b in bikes if b["status"] in ("Rented", "Overdue")),
        unread=unread_count(session["username"]),
    )


@app.route("/admin")
@admin_required
def admin_home():
    check_overdue()
    init_gps_from_rentals()
    bikes = get_motorcycles()
    rentals = get_rentals()
    pending = [r for r in rentals if r.get("status") == "Pending Confirmation"]
    return render_template(
        "admin_home.html", user=current_user(), bikes=bikes, rentals=rentals,
        pending_count=len(pending),
        available=sum(1 for b in bikes if b["status"] == "Available"),
        reserved=sum(1 for b in bikes if b["status"] == "Reserved"),
        rented=sum(1 for b in bikes if b["status"] in ("Rented", "Overdue")),
        open_support=open_support_count(),
        unread=unread_count(session["username"]),
    )


# Register remaining routes (rent, support, GPS, payments, returns)
try:
    from motoqr_routes import register_routes
    register_routes(app)
except Exception as _route_err:
    # Keep core app alive even if extra routes fail to load
    print("WARNING: motoqr_routes failed:", _route_err)


ensure_dirs()
if not os.path.exists(MOTORCYCLES_FILE):
    save_motorcycles(default_motorcycles())
if not os.path.exists(USERS_FILE):
    save_users([{"username": "admin", "password": "1234", "role": "Admin"}])
for f, default in [
    (RENTALS_FILE, []), (RETURNS_FILE, []),
    (NOTIFICATIONS_FILE, []), (SUPPORT_FILE, []),
]:
    if not os.path.exists(f):
        save_json(f, default)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)
