# =====================================================================
#  MotoQR — Web Application (multi-device / online)
# =====================================================================

from flask import (
    Flask, render_template, request, redirect, url_for,
    session, flash, jsonify, send_from_directory
)
from datetime import datetime, timedelta
from functools import wraps
from werkzeug.utils import secure_filename
import json
import os
import random

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "motoqr-dev-secret-change-in-prod")
app.config["MAX_CONTENT_LENGTH"] = 8 * 1024 * 1024  # 8 MB uploads

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")
IMAGE_DIR = os.path.join(BASE_DIR, "image")
USERS_FILE = os.path.join(DATA_DIR, "users.json")
MOTORCYCLES_FILE = os.path.join(DATA_DIR, "motorcycles.json")
RENTALS_FILE = os.path.join(DATA_DIR, "rentals.json")
RETURNS_FILE = os.path.join(DATA_DIR, "return_requests.json")
NOTIFICATIONS_FILE = os.path.join(DATA_DIR, "notifications.json")
CAPTURED_IDS_DIR = os.path.join(BASE_DIR, "captured_ids")

LATE_FEE_PER_DAY = 100
GPS_CENTER_LAT = 14.5995
GPS_CENTER_LNG = 120.9842

gps_positions = {}


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
    except (json.JSONDecodeError, OSError, TypeError):
        pass
    return default


def save_json(path, data):
    ensure_dirs()
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def default_motorcycles():
    bikes = []
    names = [
        ("M001", "Honda Click 125i", 500),
        ("M002", "Yamaha Mio Sporty", 450),
        ("M003", "Honda Beat", 400),
        ("M004", "Yamaha Aerox", 700),
        ("M005", "Honda ADV 160", 800),
        ("M006", "Yamaha NMAX", 750),
        ("M007", "Honda PCX 160", 750),
        ("M008", "Suzuki Raider 150", 600),
        ("M009", "Honda XRM 125", 550),
        ("M010", "Yamaha Sniper 155", 650),
        ("M011", "Honda CBR150R", 900),
        ("M012", "Yamaha R15", 950),
        ("M013", "Kawasaki Ninja 400", 1200),
        ("M014", "Yamaha MT-15", 850),
        ("M015", "Honda CB150R", 800),
        ("M016", "Suzuki Burgman Street", 550),
        ("M017", "Yamaha Fazzio", 500),
        ("M018", "Honda Airblade 160", 700),
        ("M019", "Kawasaki Rouser NS160", 700),
        ("M020", "Suzuki Raider R150", 650),
    ]
    for mid, name, rate in names:
        bikes.append({
            "id": mid, "name": name, "rate": rate,
            "status": "Available", "image": f"image/{mid}.jpg",
        })
    return bikes


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


def save_users(users):
    save_json(USERS_FILE, users)


def save_motorcycles(bikes):
    save_json(MOTORCYCLES_FILE, bikes)


def save_rentals(rentals):
    save_json(RENTALS_FILE, rentals)


def save_returns(returns):
    save_json(RETURNS_FILE, returns)


def save_notifications(notes):
    save_json(NOTIFICATIONS_FILE, notes)


def notify(username, title, message, ntype="info"):
    notes = get_notifications()
    notes.append({
        "id": f"N{datetime.now().strftime('%Y%m%d%H%M%S')}{random.randint(100, 999)}",
        "username": username,
        "title": title,
        "message": message,
        "type": ntype,
        "read": False,
        "date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    })
    save_notifications(notes)


def notify_admins(title, message, ntype="info"):
    for u in get_users():
        if u.get("role") == "Admin":
            notify(u["username"], title, message, ntype)


def unread_count(username):
    return sum(
        1 for n in get_notifications()
        if n.get("username") == username and not n.get("read")
    )


def user_notifications(username):
    items = [n for n in get_notifications() if n.get("username") == username]
    items.sort(key=lambda n: n.get("date", ""), reverse=True)
    return items


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
            notify(
                rental["username"],
                "Rental Overdue — Late Fee Applied",
                (
                    f"Your rental of {rental['motorcycle']} is overdue by {od} day(s).\n"
                    f"Late fee: ₱{LATE_FEE_PER_DAY}/day. Current fee: ₱{fee}.\n"
                    f"Please return the unit as soon as possible."
                ),
                ntype="danger",
            )
            notify_admins(
                "Overdue Rental Alert",
                f"{rental['username']} — {rental['motorcycle']} · {od} day(s) · ₱{fee}",
                ntype="warning",
            )
            rental["overdue_notified"] = True
            changed = True
    if changed:
        save_rentals(rentals)


def start_gps(motorcycle_id, name, username):
    gps_positions[motorcycle_id] = {
        "lat": GPS_CENTER_LAT + random.uniform(-0.03, 0.03),
        "lng": GPS_CENTER_LNG + random.uniform(-0.03, 0.03),
        "name": name,
        "username": username,
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
            flash("Please log in first.", "warning")
            return redirect(url_for("login"))
        if session.get("role") != "Admin":
            flash("Admin access only.", "danger")
            return redirect(url_for("client_home"))
        return f(*args, **kwargs)
    return wrapped


def current_user():
    return {
        "username": session.get("username"),
        "role": session.get("role"),
    }


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
        for user in get_users():
            if user["username"] == username and user["password"] == password:
                session["username"] = user["username"]
                session["role"] = user["role"]
                flash(f"Welcome, {username}!", "success")
                if user["role"] == "Admin":
                    return redirect(url_for("admin_home"))
                return redirect(url_for("client_home"))
        flash("Incorrect username or password.", "danger")
    return render_template("login.html")


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        if not username or not password:
            flash("Please enter username and password.", "warning")
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
    items = user_notifications(session["username"])
    notes = get_notifications()
    for n in notes:
        if n.get("username") == session["username"]:
            n["read"] = True
    save_notifications(notes)
    return render_template(
        "notifications.html",
        user=current_user(),
        items=items,
        unread=0,
    )


@app.route("/client")
@login_required
def client_home():
    if session.get("role") == "Admin":
        return redirect(url_for("admin_home"))
    check_overdue()
    bikes = get_motorcycles()
    available = sum(1 for b in bikes if b["status"] == "Available")
    reserved = sum(1 for b in bikes if b["status"] == "Reserved")
    rented = sum(1 for b in bikes if b["status"] in ("Rented", "Overdue"))
    return render_template(
        "client_home.html",
        user=current_user(),
        bikes=bikes,
        available=available,
        reserved=reserved,
        rented=rented,
        unread=unread_count(session["username"]),
    )


@app.route("/rent/<bike_id>", methods=["GET", "POST"])
@login_required
def rent(bike_id):
    if session.get("role") == "Admin":
        return redirect(url_for("admin_home"))
    bikes = get_motorcycles()
    bike = next((b for b in bikes if b["id"] == bike_id), None)
    if not bike:
        flash("Motorcycle not found.", "danger")
        return redirect(url_for("client_home"))
    if bike["status"] != "Available":
        flash(f"This unit is currently {bike['status'].lower()}.", "warning")
        return redirect(url_for("client_home"))

    if request.method == "POST":
        contact = request.form.get("contact", "").strip()
        try:
            days = int(request.form.get("days", "0"))
            if days <= 0:
                raise ValueError
        except Exception:
            flash("Enter a valid number of days.", "warning")
            return render_template("rent.html", user=current_user(), bike=bike,
                                   unread=unread_count(session["username"]))
        if not contact:
            flash("Contact number is required.", "warning")
            return render_template("rent.html", user=current_user(), bike=bike,
                                   unread=unread_count(session["username"]))
        method = request.form.get("payment_method", "Cash")
        ref = request.form.get("payment_ref", "").strip()
        if method == "Cash":
            ref = "CASH-ON-PICKUP"
        elif method == "GCash":
            if not ref:
                flash("Enter GCash reference number.", "warning")
                return render_template("rent.html", user=current_user(), bike=bike,
                                       unread=unread_count(session["username"]))
        elif method == "Card":
            if not ref:
                flash("Enter last 4 digits of card / reference.", "warning")
                return render_template("rent.html", user=current_user(), bike=bike,
                                       unread=unread_count(session["username"]))
            ref = f"CARD-{ref[-4:]}"

        id_file = request.files.get("id_document")
        id_path = ""
        if not id_file or not id_file.filename:
            flash("Please upload a valid ID or driver's license.", "warning")
            return render_template("rent.html", user=current_user(), bike=bike,
                                   unread=unread_count(session["username"]))
        ensure_dirs()
        ext = os.path.splitext(id_file.filename)[1].lower()
        if ext not in (".jpg", ".jpeg", ".png", ".webp", ".pdf"):
            flash("ID must be an image (JPG/PNG/WEBP) or PDF.", "warning")
            return render_template("rent.html", user=current_user(), bike=bike,
                                   unread=unread_count(session["username"]))
        safe = secure_filename(
            f"{session['username']}_{bike['id']}_{datetime.now().strftime('%Y%m%d%H%M%S')}{ext}"
        )
        save_path = os.path.join(CAPTURED_IDS_DIR, safe)
        id_file.save(save_path)
        id_path = safe

        total = bike["rate"] * days
        rentals = get_rentals()
        rental = {
            "username": session["username"],
            "customer": session["username"],
            "contact": contact,
            "motorcycle": bike["name"],
            "motorcycle_id": bike["id"],
            "days": days,
            "rate": bike["rate"],
            "total": total,
            "payment_method": method,
            "payment_ref": ref,
            "id_document": id_path,
            "date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "status": "Pending Confirmation",
            "late_fee": 0,
            "overdue_days": 0,
            "overdue_notified": False,
        }
        rentals.append(rental)
        bike["status"] = "Reserved"
        save_rentals(rentals)
        save_motorcycles(bikes)

        pay_hint = (
            f"Verify reference: {ref}"
            if method != "Cash"
            else "Collect cash at the counter."
        )
        notify_admins(
            "New Payment Awaiting Confirmation",
            (
                f"Client: {session['username']}\n"
                f"Motorcycle: {bike['name']}\n"
                f"Method: {method} · Ref: {ref}\n"
                f"Total: ₱{total}\n{pay_hint}"
            ),
            ntype="warning",
        )
        notify(
            session["username"],
            "Payment Submitted — Awaiting Admin Confirmation",
            (
                f"Rental request for {bike['name']} submitted.\n"
                f"Method: {method} · Ref: {ref}\nTotal: ₱{total}\n"
                f"You will be notified when an admin confirms."
            ),
            ntype="info",
        )
        flash("Payment submitted. Waiting for admin confirmation.", "success")
        return redirect(url_for("my_rentals"))

    return render_template(
        "rent.html",
        user=current_user(),
        bike=bike,
        unread=unread_count(session["username"]),
    )


@app.route("/my-rentals")
@login_required
def my_rentals():
    check_overdue()
    rentals = [r for r in get_rentals() if r["username"] == session["username"]]
    rentals = list(reversed(rentals))
    return render_template(
        "my_rentals.html",
        user=current_user(),
        rentals=rentals,
        unread=unread_count(session["username"]),
    )


@app.route("/return", methods=["GET", "POST"])
@login_required
def return_rent():
    active = [
        r for r in get_rentals()
        if r["username"] == session["username"]
        and r["status"] in ("Rented", "Overdue")
    ]
    if request.method == "POST":
        motorcycle = request.form.get("motorcycle", "")
        message = request.form.get("message", "").strip()
        if not motorcycle or not message:
            flash("Select a motorcycle and enter a message.", "warning")
            return render_template(
                "return.html", user=current_user(), active=active,
                unread=unread_count(session["username"]),
            )
        returns = get_returns()
        returns.append({
            "username": session["username"],
            "customer": session["username"],
            "motorcycle": motorcycle,
            "message": message,
            "date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "status": "Pending",
        })
        save_returns(returns)
        notify_admins(
            "New Return Request",
            f"{session['username']} requested to return {motorcycle}.\n{message}",
            ntype="info",
        )
        flash("Return request sent to admin.", "success")
        return redirect(url_for("my_rentals"))

    if not active:
        flash("You don't have an active rental.", "info")
        return redirect(url_for("client_home"))
    return render_template(
        "return.html",
        user=current_user(),
        active=active,
        unread=unread_count(session["username"]),
    )


@app.route("/admin")
@admin_required
def admin_home():
    check_overdue()
    init_gps_from_rentals()
    bikes = get_motorcycles()
    rentals = get_rentals()
    returns = get_returns()
    stats = {
        "total": len(bikes),
        "available": sum(1 for b in bikes if b["status"] == "Available"),
        "rented": sum(1 for b in bikes if b["status"] in ("Rented", "Overdue")),
        "pending_pay": sum(1 for r in rentals if r.get("status") == "Pending Confirmation"),
        "returns": sum(1 for r in returns if r["status"] == "Pending"),
        "overdue": sum(1 for r in rentals if r.get("status") == "Overdue"),
    }
    return render_template(
        "admin_home.html",
        user=current_user(),
        bikes=bikes,
        stats=stats,
        unread=unread_count(session["username"]),
    )


@app.route("/admin/pending-payments", methods=["GET", "POST"])
@admin_required
def pending_payments():
    rentals = get_rentals()
    if request.method == "POST":
        action = request.form.get("action")
        idx = request.form.get("index")
        try:
            idx = int(idx)
        except Exception:
            flash("Invalid selection.", "danger")
            return redirect(url_for("pending_payments"))
        pending = [r for r in rentals if r.get("status") == "Pending Confirmation"]
        if idx < 0 or idx >= len(pending):
            flash("Invalid selection.", "danger")
            return redirect(url_for("pending_payments"))
        rental = pending[idx]
        bikes = get_motorcycles()
        if action == "confirm":
            rental["status"] = "Rented"
            for bike in bikes:
                if bike["id"] == rental.get("motorcycle_id") or bike["name"] == rental["motorcycle"]:
                    bike["status"] = "Rented"
                    break
            start_gps(
                rental.get("motorcycle_id", rental["motorcycle"]),
                rental["motorcycle"],
                rental["username"],
            )
            save_rentals(rentals)
            save_motorcycles(bikes)
            notify(
                rental["username"],
                "Payment Confirmed — Rental Active",
                (
                    f"Admin confirmed payment for {rental['motorcycle']}.\n"
                    f"Method: {rental.get('payment_method')} · Ref: {rental.get('payment_ref')}\n"
                    f"Total: ₱{rental['total']}\nYour rental is now active. Ride safe!"
                ),
                ntype="success",
            )
            flash("Payment confirmed. Client notified.", "success")
        elif action == "reject":
            rental["status"] = "Payment Rejected"
            for bike in bikes:
                if bike["id"] == rental.get("motorcycle_id") or bike["name"] == rental["motorcycle"]:
                    bike["status"] = "Available"
                    break
            save_rentals(rentals)
            save_motorcycles(bikes)
            notify(
                rental["username"],
                "Payment Rejected",
                (
                    f"Admin rejected payment for {rental['motorcycle']}.\n"
                    f"Please contact the shop or submit a new rental."
                ),
                ntype="danger",
            )
            flash("Payment rejected. Client notified.", "info")
        return redirect(url_for("pending_payments"))

    pending = [r for r in rentals if r.get("status") == "Pending Confirmation"]
    return render_template(
        "pending_payments.html",
        user=current_user(),
        pending=pending,
        unread=unread_count(session["username"]),
    )


@app.route("/admin/rentals")
@admin_required
def all_rentals():
    check_overdue()
    rentals = list(reversed(get_rentals()))
    return render_template(
        "all_rentals.html",
        user=current_user(),
        rentals=rentals,
        unread=unread_count(session["username"]),
    )


@app.route("/admin/returns", methods=["GET", "POST"])
@admin_required
def return_requests():
    returns = get_returns()
    if request.method == "POST":
        action = request.form.get("action")
        try:
            idx = int(request.form.get("index", "-1"))
        except Exception:
            flash("Invalid selection.", "danger")
            return redirect(url_for("return_requests"))
        pending = [r for r in returns if r["status"] == "Pending"]
        if idx < 0 or idx >= len(pending):
            flash("Invalid selection.", "danger")
            return redirect(url_for("return_requests"))
        req = pending[idx]
        if action == "approve":
            req["status"] = "Approved"
            rentals = get_rentals()
            mid = None
            for rental in rentals:
                if (
                    rental["username"] == req["username"]
                    and rental["motorcycle"] == req["motorcycle"]
                    and rental["status"] in ("Rented", "Overdue")
                ):
                    rental["status"] = "Returned"
                    mid = rental.get("motorcycle_id")
                    break
            bikes = get_motorcycles()
            for bike in bikes:
                if bike["name"] == req["motorcycle"]:
                    bike["status"] = "Available"
                    mid = mid or bike["id"]
                    break
            if mid:
                stop_gps(mid)
            save_returns(returns)
            save_rentals(rentals)
            save_motorcycles(bikes)
            notify(
                req["username"],
                "Return Approved",
                f"Admin approved the return of {req['motorcycle']}. Thank you!",
                ntype="success",
            )
            flash("Return approved. Client notified.", "success")
        elif action == "reject":
            req["status"] = "Rejected"
            save_returns(returns)
            notify(
                req["username"],
                "Return Request Rejected",
                f"Admin rejected your return request for {req['motorcycle']}.",
                ntype="warning",
            )
            flash("Return rejected. Client notified.", "info")
        return redirect(url_for("return_requests"))

    pending = [r for r in returns if r["status"] == "Pending"]
    return render_template(
        "return_requests.html",
        user=current_user(),
        pending=pending,
        unread=unread_count(session["username"]),
    )


@app.route("/admin/gps")
@admin_required
def gps_tracker():
    init_gps_from_rentals()
    tick_gps()
    active = [r for r in get_rentals() if r.get("status") in ("Rented", "Overdue")]
    units = []
    for r in active:
        mid = r.get("motorcycle_id") or r["motorcycle"]
        if mid not in gps_positions:
            start_gps(mid, r["motorcycle"], r["username"])
        pos = gps_positions[mid]
        units.append({
            "id": mid,
            "name": r["motorcycle"],
            "username": r["username"],
            "status": r["status"],
            "lat": round(pos["lat"], 5),
            "lng": round(pos["lng"], 5),
            "updated": pos["updated"],
        })
    return render_template(
        "gps.html",
        user=current_user(),
        units=units,
        unread=unread_count(session["username"]),
    )


@app.route("/api/gps")
@admin_required
def api_gps():
    init_gps_from_rentals()
    tick_gps()
    active = [r for r in get_rentals() if r.get("status") in ("Rented", "Overdue")]
    units = []
    for r in active:
        mid = r.get("motorcycle_id") or r["motorcycle"]
        if mid not in gps_positions:
            start_gps(mid, r["motorcycle"], r["username"])
        pos = gps_positions[mid]
        units.append({
            "id": mid,
            "name": r["motorcycle"],
            "username": r["username"],
            "status": r["status"],
            "lat": round(pos["lat"], 5),
            "lng": round(pos["lng"], 5),
            "updated": pos["updated"],
        })
    return jsonify(units)


@app.route("/admin/users")
@admin_required
def users_list():
    return render_template(
        "users.html",
        user=current_user(),
        users=get_users(),
        unread=unread_count(session["username"]),
    )


ensure_dirs()
if not os.path.exists(MOTORCYCLES_FILE):
    save_motorcycles(default_motorcycles())
if not os.path.exists(USERS_FILE):
    save_users([{"username": "admin", "password": "1234", "role": "Admin"}])
for f, default in [
    (RENTALS_FILE, []),
    (RETURNS_FILE, []),
    (NOTIFICATIONS_FILE, []),
]:
    if not os.path.exists(f):
        save_json(f, default)


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)
