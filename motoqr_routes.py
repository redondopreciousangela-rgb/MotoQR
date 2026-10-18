"""Extra routes registered onto the main Flask app."""
from datetime import datetime, timedelta
from io import BytesIO
import os
import random
from flask import (
    request, redirect, url_for, session, flash, jsonify, render_template, send_file, abort
)
from werkzeug.utils import secure_filename


def register_routes(app):
    from app import (
        login_required, admin_required, current_user, get_motorcycles,
        get_rentals, get_returns, get_notifications, get_support_messages,
        save_motorcycles, save_rentals, save_returns, save_notifications,
        save_support_messages, notify, notify_admins, unread_count,
        normalize_phone, ensure_dirs, client_active_rentals, client_contact,
        open_support_count, start_gps, stop_gps, tick_gps, init_gps_from_rentals,
        check_overdue, gps_positions, CAPTURED_IDS_DIR, LATE_FEE_PER_DAY,
        get_users, save_users,
    )

    def motorcycle_category(bike):
        if bike.get("category"):
            return bike["category"]
        name = (bike.get("name") or "").lower()
        if any(x in name for x in ("crf", "klx", "dirt", "wr250")):
            return "Dirt Bike"
        if any(x in name for x in ("ninja", "cbr", "r15", "400", "mt-15", "cb150r")):
            return "Big Bike"
        if any(x in name for x in ("click", "mio", "beat", "aerox", "adv", "nmax", "pcx", "burgman", "fazzio", "airblade")):
            return "Scooter"
        if any(x in name for x in ("raider", "sniper", "xrm", "rouser")):
            return "Underbone"
        return "Standard"

    def motorcycle_is_new(bike):
        created = bike.get("created_at")
        if not created:
            return False
        try:
            dt = datetime.fromisoformat(created)
            return datetime.now() - dt <= timedelta(days=7)
        except (TypeError, ValueError):
            return False

    @app.route("/motorcycle/<bike_id>")
    def motorcycle_status(bike_id):
        bike = next((b for b in get_motorcycles() if b.get("id") == bike_id), None)
        if not bike:
            abort(404)
        return render_template(
            "motorcycle_status.html", bike=bike,
            category=motorcycle_category(bike), is_new=motorcycle_is_new(bike),
            checked_at=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        )

    @app.route("/api/motorcycle/<bike_id>")
    def api_motorcycle_status(bike_id):
        bike = next((b for b in get_motorcycles() if b.get("id") == bike_id), None)
        if not bike:
            return jsonify({"ok": False, "error": "not_found"}), 404
        return jsonify({
            "ok": True, "id": bike.get("id"), "name": bike.get("name"),
            "status": bike.get("status", "Unknown"),
            "category": motorcycle_category(bike),
            "maintenance_status": bike.get("maintenance_status", "Up to date"),
            "maintenance_notes": bike.get("maintenance_notes", ""),
            "maintenance_updated": bike.get("maintenance_updated", "Not recorded"),
            "is_new": motorcycle_is_new(bike),
            "checked_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        })

    @app.route("/motorcycle/<bike_id>/qr.png")
    def motorcycle_qr(bike_id):
        bike = next((b for b in get_motorcycles() if b.get("id") == bike_id), None)
        if not bike:
            abort(404)
        try:
            import qrcode
            target = request.url_root.rstrip("/") + url_for("motorcycle_status", bike_id=bike_id)
            image = qrcode.make(target)
            stream = BytesIO()
            image.save(stream, format="PNG")
            stream.seek(0)
            return send_file(stream, mimetype="image/png", download_name=f"{bike_id}-qr.png")
        except Exception:
            flash("Could not generate QR code. Check that the qrcode package is installed.", "danger")
            return redirect(url_for("admin_home"))

    @app.route("/admin/motorcycle/<bike_id>/maintenance", methods=["POST"])
    @admin_required
    def update_motorcycle_maintenance(bike_id):
        bikes = get_motorcycles()
        bike = next((b for b in bikes if b.get("id") == bike_id), None)
        if not bike:
            abort(404)
        valid = ("Up to date", "Due soon", "In maintenance", "Out of service")
        state = request.form.get("maintenance_status", "Up to date")
        if state not in valid:
            state = "Up to date"
        # Keep the fleet status consistent with maintenance, and restore active
        # rental states when maintenance is cleared.
        blocked_states = ("In maintenance", "Out of service")
        previous_maintenance = bike.get("maintenance_status", "Up to date")
        if state in blocked_states:
            if previous_maintenance not in blocked_states:
                bike["maintenance_previous_status"] = bike.get("status", "Available")
            bike["status"] = state
        else:
            active_rentals = [
                rental for rental in get_rentals()
                if rental.get("motorcycle_id") == bike_id
                and rental.get("status") in ("Pending Confirmation", "Rented", "Overdue")
            ]
            current_rental = next(
                (r for r in active_rentals if r.get("status") in ("Rented", "Overdue")),
                None,
            )
            pending_rental = next(
                (r for r in active_rentals if r.get("status") == "Pending Confirmation"),
                None,
            )
            if current_rental:
                bike["status"] = current_rental.get("status", "Rented")
            elif pending_rental:
                bike["status"] = "Reserved"
            else:
                bike["status"] = "Available"
            bike.pop("maintenance_previous_status", None)
        bike["maintenance_status"] = state
        bike["maintenance_notes"] = request.form.get("maintenance_notes", "").strip()[:500]
        bike["maintenance_updated"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        save_motorcycles(bikes)
        flash(f"Maintenance details updated for {bike.get('name', bike_id)}.", "success")
        return redirect(url_for("admin_home"))

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
        if bike.get("maintenance_status") in ("In maintenance", "Out of service"):
            flash(f"This unit is currently {bike['maintenance_status'].lower()} and cannot be rented.", "warning")
            return redirect(url_for("client_home"))
        if bike.get("status") != "Available":
            flash(f"This unit is currently {bike.get('status', 'unavailable').lower()}.", "warning")
            return redirect(url_for("client_home"))
        if request.method == "POST":
            contact = normalize_phone(request.form.get("contact", "").strip())
            try:
                days = int(request.form.get("days", "0"))
                if days <= 0:
                    raise ValueError
            except Exception:
                flash("Enter a valid number of days.", "warning")
                return render_template("rent.html", user=current_user(), bike=bike,
                                       unread=unread_count(session["username"]))
            if not contact or len(contact) < 10 or len(contact) > 13:
                flash("Enter a valid phone number (10-13 digits).", "warning")
                return render_template("rent.html", user=current_user(), bike=bike,
                                       unread=unread_count(session["username"]))
            method = request.form.get("payment_method", "Cash")
            ref = request.form.get("payment_ref", "").strip()
            if method == "Cash":
                ref = "CASH-ON-PICKUP"
            elif method in ("GCash", "Card") and not ref:
                flash("Enter payment reference.", "warning")
                return render_template("rent.html", user=current_user(), bike=bike,
                                       unread=unread_count(session["username"]))
            if method == "Card" and ref:
                ref = f"CARD-{ref[-4:]}"
            id_file = request.files.get("id_document")
            if not id_file or not id_file.filename:
                flash("Please upload a valid ID or driver's license.", "warning")
                return render_template("rent.html", user=current_user(), bike=bike,
                                       unread=unread_count(session["username"]))
            ensure_dirs()
            ext = os.path.splitext(id_file.filename)[1].lower()
            if ext not in (".jpg", ".jpeg", ".png", ".webp", ".pdf"):
                flash("ID must be an image or PDF.", "warning")
                return render_template("rent.html", user=current_user(), bike=bike,
                                       unread=unread_count(session["username"]))
            safe = secure_filename(
                f"{session['username']}_{bike['id']}_{datetime.now().strftime('%Y%m%d%H%M%S')}{ext}"
            )
            id_file.save(os.path.join(CAPTURED_IDS_DIR, safe))
            total = bike["rate"] * days
            rentals = get_rentals()
            rental = {
                "id": f"R{datetime.now().strftime('%Y%m%d%H%M%S')}{random.randint(10, 99)}",
                "username": session["username"],
                "motorcycle": bike["name"],
                "motorcycle_id": bike["id"],
                "days": days,
                "total": total,
                "contact": contact,
                "payment_method": method,
                "payment_ref": ref,
                "id_document": safe,
                "status": "Pending Confirmation",
                "date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "late_fee": 0,
            }
            rentals.append(rental)
            save_rentals(rentals)
            bike["status"] = "Reserved"
            save_motorcycles(bikes)
            notify_admins(
                "New Rental Pending",
                f"{session['username']} rented {bike['name']} for {days} day(s).\n"
                f"Payment: {method} ({ref})\nTotal: PHP {total}",
                ntype="warning",
            )
            notify(
                session["username"],
                "Rental Submitted",
                f"Your rental of {bike['name']} is pending admin confirmation.",
                ntype="info",
            )
            flash("Rental submitted. Waiting for admin confirmation.", "success")
            return redirect(url_for("my_rentals"))
        return render_template("rent.html", user=current_user(), bike=bike,
                               unread=unread_count(session["username"]))

    @app.route("/my-rentals")
    @login_required
    def my_rentals():
        check_overdue()
        rentals = [r for r in get_rentals() if r.get("username") == session["username"]]
        rentals.sort(key=lambda r: r.get("date", ""), reverse=True)
        return render_template("my_rentals.html", user=current_user(), rentals=rentals,
                               unread=unread_count(session["username"]))

    @app.route("/admin/pending-payments", methods=["GET", "POST"])
    @admin_required
    def pending_payments():
        rentals = get_rentals()
        if request.method == "POST":
            rid = request.form.get("rental_id")
            action = request.form.get("action")
            rental = next((r for r in rentals if r.get("id") == rid), None)
            if rental and rental.get("status") == "Pending Confirmation":
                bikes = get_motorcycles()
                bike = next((b for b in bikes if b["id"] == rental.get("motorcycle_id")), None)
                if action == "confirm":
                    if bike and bike.get("maintenance_status") in ("In maintenance", "Out of service"):
                        flash("Cannot confirm this rental: the motorcycle is unavailable for maintenance.", "warning")
                    else:
                        rental["status"] = "Rented"
                        if bike:
                            bike["status"] = "Rented"
                        start_gps(rental.get("motorcycle_id"), rental.get("motorcycle"),
                                  rental.get("username"))
                        notify(rental["username"], "Payment Confirmed",
                               f"Your rental of {rental['motorcycle']} is confirmed. Enjoy the ride!",
                               ntype="success")
                        flash("Rental confirmed.", "success")
                elif action == "reject":
                    rental["status"] = "Cancelled"
                    if bike:
                        bike["status"] = (
                            bike.get("maintenance_status")
                            if bike.get("maintenance_status") in ("In maintenance", "Out of service")
                            else "Available"
                        )
                    notify(rental["username"], "Rental Rejected",
                           f"Your rental of {rental['motorcycle']} was not approved.",
                           ntype="danger")
                    flash("Rental rejected.", "info")
                save_rentals(rentals)
                save_motorcycles(bikes)
            return redirect(url_for("pending_payments"))
        pending = [r for r in rentals if r.get("status") == "Pending Confirmation"]
        return render_template("pending_payments.html", user=current_user(),
                               pending=pending, unread=unread_count(session["username"]))

    @app.route("/admin/all-rentals")
    @admin_required
    def all_rentals():
        check_overdue()
        rentals = sorted(
            [r for r in get_rentals() if r.get("status") in ("Rented", "Overdue")],
            key=lambda r: r.get("date", ""), reverse=True,
        )
        return render_template("all_rentals.html", user=current_user(), rentals=rentals,
                               unread=unread_count(session["username"]))

    @app.route("/admin/gps")
    @admin_required
    def gps_tracker():
        init_gps_from_rentals()
        tick_gps()
        return render_template("gps.html", user=current_user(), positions=gps_positions,
                               unread=unread_count(session["username"]))

    @app.route("/api/gps")
    @admin_required
    def api_gps():
        init_gps_from_rentals()
        tick_gps()
        return jsonify(gps_positions)

    @app.route("/admin/add-motorcycle", methods=["GET", "POST"])
    @admin_required
    def add_motorcycle():
        if request.method == "POST":
            mid = request.form.get("id", "").strip().upper()
            name = request.form.get("name", "").strip()
            try:
                rate = int(request.form.get("rate", "0"))
            except Exception:
                rate = 0
            if not mid or not name or rate <= 0:
                flash("Fill all fields with a valid rate.", "warning")
            else:
                bikes = get_motorcycles()
                if any(b["id"] == mid for b in bikes):
                    flash("ID already exists.", "danger")
                else:
                    category = request.form.get("category", "Standard")
                    if category not in ("Scooter", "Big Bike", "Dirt Bike", "Underbone", "Standard"):
                        category = "Standard"
                    maintenance_status = request.form.get("maintenance_status", "Up to date")
                    if maintenance_status not in ("Up to date", "Due soon", "In maintenance", "Out of service"):
                        maintenance_status = "Up to date"
                    bikes.append({
                        "id": mid, "name": name, "rate": rate,
                        "status": maintenance_status if maintenance_status in ("In maintenance", "Out of service") else "Available",
                        "image": f"image/{mid}.jpg",
                        "category": category, "created_at": datetime.now().isoformat(timespec="seconds"),
                        "maintenance_status": maintenance_status,
                        "maintenance_notes": request.form.get("maintenance_notes", "").strip()[:500],
                    })
                    save_motorcycles(bikes)
                    flash(f"Added {name}.", "success")
                    return redirect(url_for("admin_home"))
        return render_template("add_motorcycle.html", user=current_user(),
                               unread=unread_count(session["username"]))

    @app.route("/admin/users")
    @admin_required
    def users_list():
        return render_template("users.html", user=current_user(), users=get_users(),
                               unread=unread_count(session["username"]))

    @app.route("/return", methods=["GET", "POST"])
    @login_required
    def return_unit():
        if session.get("role") == "Admin":
            return redirect(url_for("admin_home"))
        active = [r for r in get_rentals()
                  if r.get("username") == session["username"]
                  and r.get("status") in ("Rented", "Overdue")]
        if request.method == "POST":
            rid = request.form.get("rental_id")
            rental = next((r for r in active if r.get("id") == rid), None)
            if not rental:
                flash("Select a valid rental.", "warning")
            else:
                returns = get_returns()
                returns.append({
                    "id": f"RT{datetime.now().strftime('%Y%m%d%H%M%S')}",
                    "rental_id": rid,
                    "username": session["username"],
                    "motorcycle": rental.get("motorcycle"),
                    "date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "status": "Pending",
                })
                save_returns(returns)
                notify_admins("Return Request",
                              f"{session['username']} wants to return {rental.get('motorcycle')}",
                              ntype="info")
                flash("Return request submitted.", "success")
                return redirect(url_for("my_rentals"))
        return render_template("return.html", user=current_user(), rentals=active,
                               unread=unread_count(session["username"]))

    @app.route("/admin/return-requests", methods=["GET", "POST"])
    @admin_required
    def return_requests():
        returns = get_returns()
        if request.method == "POST":
            rid = request.form.get("request_id")
            action = request.form.get("action")
            req = next((r for r in returns if r.get("id") == rid), None)
            if req and req.get("status") == "Pending":
                rentals = get_rentals()
                rental = next((r for r in rentals if r.get("id") == req.get("rental_id")), None)
                if action == "approve" and rental:
                    req["status"] = "Approved"
                    rental["status"] = "Returned"
                    bikes = get_motorcycles()
                    bike = next((b for b in bikes if b["id"] == rental.get("motorcycle_id")), None)
                    if bike:
                        bike["status"] = (
                            bike.get("maintenance_status")
                            if bike.get("maintenance_status") in ("In maintenance", "Out of service")
                            else "Available"
                        )
                    stop_gps(rental.get("motorcycle_id"))
                    save_motorcycles(bikes)
                    save_rentals(rentals)
                    notify(req["username"], "Return Approved",
                           f"Return of {req.get('motorcycle')} approved. Thank you!",
                           ntype="success")
                    flash("Return approved.", "success")
                elif action == "reject":
                    req["status"] = "Rejected"
                    notify(req["username"], "Return Rejected",
                           f"Return of {req.get('motorcycle')} was rejected. Contact support.",
                           ntype="warning")
                    flash("Return rejected.", "info")
                save_returns(returns)
            return redirect(url_for("return_requests"))
        pending = [r for r in returns if r.get("status") == "Pending"]
        return render_template("return_requests.html", user=current_user(),
                               requests=pending, unread=unread_count(session["username"]))

    @app.route("/support", methods=["GET", "POST"])
    @login_required
    def customer_service():
        if session.get("role") == "Admin":
            return redirect(url_for("admin_support"))
        threads = [m for m in get_support_messages()
                   if m.get("username") == session["username"]]
        threads.sort(key=lambda m: m.get("updated") or m.get("date") or "", reverse=True)
        if request.method == "POST":
            subject = request.form.get("subject", "").strip()
            body = request.form.get("message", "").strip()
            motorcycle = request.form.get("motorcycle", "").strip()
            active = client_active_rentals(session["username"])
            if not motorcycle and active:
                preferred = next(
                    (r for r in active if r.get("status") in ("Rented", "Overdue")),
                    active[0],
                )
                motorcycle = preferred.get("motorcycle") or ""
            contact = client_contact(session["username"])
            if not subject or not body:
                flash("Enter subject and message.", "warning")
                return redirect(url_for("customer_service"))
            now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            msgs = get_support_messages()
            ticket = {
                "id": f"CS{datetime.now().strftime('%Y%m%d%H%M%S')}{random.randint(10, 99)}",
                "username": session["username"],
                "subject": subject,
                "motorcycle": motorcycle or "—",
                "contact": contact or "—",
                "date": now, "updated": now, "status": "Open",
                "messages": [{
                    "from": "client", "username": session["username"],
                    "text": body, "date": now,
                }],
                "message": body, "admin_reply": "",
            }
            msgs.append(ticket)
            save_support_messages(msgs)
            notify_admins("New Customer Service Chat",
                          f"From: {session['username']}\nSubject: {subject}\n{body}",
                          ntype="warning")
            flash("Conversation started.", "success")
            return redirect(url_for("support_thread", ticket_id=ticket["id"]))
        active_rentals = client_active_rentals(session["username"])
        detected_unit = ""
        if active_rentals:
            preferred = next(
                (r for r in active_rentals if r.get("status") in ("Rented", "Overdue")),
                active_rentals[0],
            )
            detected_unit = preferred.get("motorcycle") or ""
        return render_template(
            "support.html", user=current_user(), threads=threads,
            active_rentals=active_rentals, detected_unit=detected_unit,
            client_phone=client_contact(session["username"]),
            unread=unread_count(session["username"]),
        )

    @app.route("/support/<ticket_id>", methods=["GET", "POST"])
    @login_required
    def support_thread(ticket_id):
        if session.get("role") == "Admin":
            return redirect(url_for("admin_support_thread", ticket_id=ticket_id))
        msgs = get_support_messages()
        ticket = next((m for m in msgs if m.get("id") == ticket_id), None)
        if not ticket or ticket.get("username") != session["username"]:
            flash("Conversation not found.", "danger")
            return redirect(url_for("customer_service"))
        if not ticket.get("messages"):
            ticket["messages"] = []
            if ticket.get("message"):
                ticket["messages"].append({
                    "from": "client", "username": ticket.get("username"),
                    "text": ticket["message"], "date": ticket.get("date", ""),
                })
        if request.method == "POST" and ticket.get("status") != "Closed":
            text = request.form.get("message", "").strip()
            if text:
                now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                ticket["messages"].append({
                    "from": "client", "username": session["username"],
                    "text": text, "date": now,
                })
                ticket["updated"] = now
                save_support_messages(msgs)
                notify_admins("Customer Service — New Message",
                              f"From: {session['username']} · {ticket.get('subject')}\n{text}",
                              ntype="warning")
            return redirect(url_for("support_thread", ticket_id=ticket_id))
        if not ticket.get("contact") or str(ticket.get("contact")).strip() in ("—", "-", "N/A"):
            ticket["contact"] = client_contact(ticket.get("username", "")) or "—"
        return render_template("support_chat.html", user=current_user(), ticket=ticket,
                               unread=unread_count(session["username"]), is_admin=False)

    @app.route("/admin/support")
    @admin_required
    def admin_support():
        threads = sorted(get_support_messages(),
                         key=lambda m: m.get("updated") or m.get("date") or "", reverse=True)
        for t in threads:
            if not t.get("contact") or str(t.get("contact")).strip() in ("—", "-", "N/A"):
                t["contact"] = client_contact(t.get("username", "")) or "—"
        return render_template("admin_support.html", user=current_user(), threads=threads,
                               open_count=open_support_count(),
                               unread=unread_count(session["username"]))

    @app.route("/admin/support/<ticket_id>", methods=["GET", "POST"])
    @admin_required
    def admin_support_thread(ticket_id):
        msgs = get_support_messages()
        ticket = next((m for m in msgs if m.get("id") == ticket_id), None)
        if not ticket:
            flash("Conversation not found.", "danger")
            return redirect(url_for("admin_support"))
        if not ticket.get("messages"):
            ticket["messages"] = []
            if ticket.get("message"):
                ticket["messages"].append({
                    "from": "client", "username": ticket.get("username"),
                    "text": ticket["message"], "date": ticket.get("date", ""),
                })
        if request.method == "POST":
            action = request.form.get("action", "reply")
            if action == "close":
                ticket["status"] = "Closed"
                ticket["updated"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                save_support_messages(msgs)
                notify(ticket["username"], "Chat Closed",
                       f"Ticket {ticket_id} was closed by support.", ntype="info")
            elif action == "reopen":
                ticket["status"] = "Open"
                ticket["updated"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                save_support_messages(msgs)
            else:
                text = request.form.get("message", "").strip()
                if text and ticket.get("status") != "Closed":
                    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    ticket["messages"].append({
                        "from": "admin", "username": session["username"],
                        "text": text, "date": now,
                    })
                    ticket["updated"] = now
                    save_support_messages(msgs)
                    notify(ticket["username"], "Support Reply",
                           f"Ticket {ticket_id}: {ticket.get('subject')}\n\n{text}",
                           ntype="success")
            return redirect(url_for("admin_support_thread", ticket_id=ticket_id))
        if not ticket.get("contact") or ticket.get("contact") == "—":
            ticket["contact"] = client_contact(ticket.get("username", "")) or "—"
        return render_template("support_chat.html", user=current_user(), ticket=ticket,
                               unread=unread_count(session["username"]), is_admin=True)

    @app.route("/api/support/<ticket_id>", methods=["GET", "POST"])
    @login_required
    def api_support_thread(ticket_id):
        msgs = get_support_messages()
        ticket = next((m for m in msgs if m.get("id") == ticket_id), None)
        if not ticket:
            return jsonify({"ok": False, "error": "not_found"}), 404
        is_admin = session.get("role") == "Admin"
        if not is_admin and ticket.get("username") != session.get("username"):
            return jsonify({"ok": False, "error": "forbidden"}), 403
        if not ticket.get("messages"):
            ticket["messages"] = []
        if request.method == "GET":
            # Older support tickets may store an em dash as a placeholder.
            # Treat it as missing so the phone number is recovered from the
            # user's rental record instead of being overwritten by the username.
            contact = ticket.get("contact")
            if not contact or str(contact).strip() in ("—", "-", "N/A"):
                contact = client_contact(ticket.get("username", ""))
            contact = contact or "—"
            return jsonify({
                "ok": True, "id": ticket["id"], "status": ticket.get("status", "Open"),
                "subject": ticket.get("subject", ""), "username": ticket.get("username", ""),
                "motorcycle": ticket.get("motorcycle", "—"), "contact": contact,
                "updated": ticket.get("updated") or ticket.get("date") or "",
                "messages": ticket.get("messages") or [],
            })
        action = request.form.get("action") or "reply"
        if action == "close" and is_admin:
            ticket["status"] = "Closed"
            ticket["updated"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            save_support_messages(msgs)
            return jsonify({"ok": True, "status": "Closed", "messages": ticket["messages"]})
        if action == "reopen" and is_admin:
            ticket["status"] = "Open"
            ticket["updated"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            save_support_messages(msgs)
            return jsonify({"ok": True, "status": "Open", "messages": ticket["messages"]})
        if ticket.get("status") == "Closed":
            return jsonify({"ok": False, "error": "closed"}), 400
        text = (request.form.get("message") or "").strip()
        if not text:
            return jsonify({"ok": False, "error": "empty"}), 400
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        entry = {
            "from": "admin" if is_admin else "client",
            "username": session["username"], "text": text, "date": now,
        }
        ticket.setdefault("messages", []).append(entry)
        ticket["updated"] = now
        ticket["status"] = "Open"
        save_support_messages(msgs)
        if is_admin:
            notify(ticket["username"], "Support Reply",
                   f"Ticket {ticket_id}: {ticket.get('subject')}\n\n{text}", ntype="success")
        else:
            notify_admins("Customer Service — New Message",
                          f"From: {session['username']} · {ticket.get('subject')}\n{text}",
                          ntype="warning")
        return jsonify({"ok": True, "status": ticket["status"],
                        "messages": ticket["messages"], "message": entry})
