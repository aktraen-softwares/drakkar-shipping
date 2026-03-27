import os
import sqlite3
import hashlib
from datetime import datetime, timedelta
from functools import wraps
from flask import (
    Flask, render_template, request, redirect, url_for,
    session, flash, jsonify, send_from_directory, abort
)

app = Flask(__name__)

# VULNERABILITY: Hardcoded secret key (discoverable via .git source leak)
app.secret_key = "drakkar-flask-secret-2026-xK9mW3pQ7vL"

# VULNERABILITY: Debug mode enabled — exposes stack traces with code context
app.debug = True

DATABASE = "/data/drakkar.db"
ADMIN_USER = "admin"
ADMIN_PASS = "DK!superadmin#2026"
AUDIT_USER = "audit"
AUDIT_PASS = "DK!audit2026"


def get_db():
    db_path = DATABASE if os.path.exists(os.path.dirname(DATABASE)) else "drakkar.db"
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            role TEXT DEFAULT 'client',
            email TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS shipments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            tracking_number TEXT UNIQUE NOT NULL,
            sender_name TEXT NOT NULL,
            receiver_name TEXT NOT NULL,
            origin TEXT NOT NULL,
            destination TEXT NOT NULL,
            status TEXT DEFAULT 'In Transit',
            weight_kg REAL,
            description TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS admin_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            action TEXT NOT NULL,
            user TEXT,
            details TEXT,
            ip_address TEXT,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    admin_hash = hashlib.sha256(ADMIN_PASS.encode()).hexdigest()
    audit_hash = hashlib.sha256(AUDIT_PASS.encode()).hexdigest()

    cursor.execute("SELECT COUNT(*) FROM users WHERE username = ?", (ADMIN_USER,))
    if cursor.fetchone()[0] == 0:
        cursor.execute(
            "INSERT INTO users (username, password_hash, role, email) VALUES (?, ?, ?, ?)",
            (ADMIN_USER, admin_hash, "admin", "admin@drakkar-shipping.is")
        )

    cursor.execute("SELECT COUNT(*) FROM users WHERE username = ?", (AUDIT_USER,))
    if cursor.fetchone()[0] == 0:
        cursor.execute(
            "INSERT INTO users (username, password_hash, role, email) VALUES (?, ?, ?, ?)",
            (AUDIT_USER, audit_hash, "auditor", "audit@drakkar-shipping.is")
        )

    sample_shipments = [
        ("DK-2026-00142", "Nordvik Fisheries", "Reykjavik Cold Storage", "Akureyri", "Reykjavik", "Delivered", 2450.0, "Frozen seafood — 12 pallets"),
        ("DK-2026-00187", "Eldfjall Metals", "Hamburg Steelworks", "Husavik", "Hamburg", "In Transit", 18500.0, "Raw aluminum ingots"),
        ("DK-2026-00203", "Borg Textiles Ltd", "London Distribution Centre", "Isafjordur", "London", "In Transit", 780.0, "Wool textiles — 40 crates"),
        ("DK-2026-00219", "Vatnajokull Energy", "Oslo Terminal", "Reydarfjordur", "Oslo", "Customs Hold", 3200.0, "Industrial equipment parts"),
        ("DK-2026-00234", "Snaefell Agriculture", "Copenhagen Harbour", "Dalvik", "Copenhagen", "Loading", 1100.0, "Organic produce — refrigerated"),
        ("DK-2026-00251", "Hekla Pharmaceuticals", "Rotterdam Port", "Reykjavik", "Rotterdam", "In Transit", 420.0, "Pharmaceutical supplies — temp controlled"),
        ("DK-2026-00268", "Grimsnes Construction", "Bergen Docks", "Vestmannaeyjar", "Bergen", "Delivered", 6800.0, "Construction materials — steel beams"),
        ("DK-2026-00275", "Thingvellir Tech", "Dublin Freight", "Keflavik", "Dublin", "Awaiting Pickup", 95.0, "Electronic components"),
    ]

    for shipment in sample_shipments:
        cursor.execute("SELECT COUNT(*) FROM shipments WHERE tracking_number = ?", (shipment[0],))
        if cursor.fetchone()[0] == 0:
            cursor.execute(
                "INSERT INTO shipments (tracking_number, sender_name, receiver_name, origin, destination, status, weight_kg, description) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                shipment
            )

    conn.commit()
    conn.close()


def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if "user" not in session:
            flash("Please log in to access this area.", "warning")
            return redirect(url_for("login"))
        return f(*args, **kwargs)
    return decorated


@app.after_request
def add_headers(response):
    # VULNERABILITY: Verbose headers leak technology stack
    response.headers["X-Powered-By"] = "Flask"
    response.headers["X-Server-Version"] = "1.2.3-dev"
    response.headers["X-Debug-Mode"] = "enabled"
    return response


# --- Public pages ---

@app.route("/")
def index():
    return render_template("index.html")


@app.route("/services")
def services():
    return render_template("services.html")


@app.route("/about")
def about():
    return render_template("about.html")


@app.route("/contact")
def contact():
    return render_template("contact.html")


@app.route("/track", methods=["GET", "POST"])
def track():
    result = None
    error = None
    if request.method == "POST":
        tracking_number = request.form.get("tracking_number", "").strip()
        if not tracking_number:
            error = "Please enter a tracking number."
        else:
            # VULNERABILITY: Special characters cause unhandled exceptions
            # which leak stack traces due to DEBUG=True
            conn = get_db()
            cursor = conn.cursor()
            cursor.execute(
                "SELECT * FROM shipments WHERE tracking_number = ?",
                (tracking_number,)
            )
            row = cursor.fetchone()
            conn.close()
            if row:
                result = dict(row)
            else:
                # Force an error path for certain inputs to trigger debug traces
                if any(c in tracking_number for c in ["'", '"', ";", "<", ">"]):
                    # Deliberately trigger an unhandled exception
                    raise ValueError(
                        f"Invalid tracking format: {tracking_number} — "
                        f"expected pattern DK-YYYY-NNNNN. "
                        f"Database path: {DATABASE}, secret: {app.secret_key}"
                    )
                error = f"No shipment found for tracking number: {tracking_number}"
    return render_template("track.html", result=result, error=error)


# --- Client area ---

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username", "")
        password = request.form.get("password", "")
        password_hash = hashlib.sha256(password.encode()).hexdigest()
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT * FROM users WHERE username = ? AND password_hash = ?",
            (username, password_hash)
        )
        user = cursor.fetchone()
        conn.close()
        if user:
            session["user"] = user["username"]
            session["role"] = user["role"]
            flash(f"Welcome back, {user['username']}.", "success")
            return redirect(url_for("client_dashboard"))
        else:
            flash("Invalid credentials.", "danger")
    return render_template("login.html")


@app.route("/logout")
def logout():
    session.clear()
    flash("You have been logged out.", "info")
    return redirect(url_for("index"))


@app.route("/client")
@login_required
def client_dashboard():
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM shipments ORDER BY updated_at DESC")
    shipments = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return render_template("client_dashboard.html", shipments=shipments)


# --- VULNERABILITY: Exposed .git directory ---

@app.route("/.git/<path:filename>")
def serve_git(filename):
    return send_from_directory("fake_git", filename)


@app.route("/.git/")
def git_index():
    files = [
        "HEAD",
        "config",
        "refs/heads/main",
        "logs/HEAD",
        "objects/",
        "COMMIT_EDITMSG",
        "description",
    ]
    listing = "<html><head><title>Index of /.git/</title></head><body>"
    listing += "<h1>Index of /.git/</h1><hr><pre>"
    listing += '<a href="/">../</a>\n'
    for f in files:
        listing += f'<a href="/.git/{f}">{f}</a>\n'
    listing += "</pre><hr></body></html>"
    return listing, 200


# --- VULNERABILITY: Undocumented admin endpoints ---

@app.route("/admin/")
@login_required
def admin_panel():
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users")
    users = [dict(row) for row in cursor.fetchall()]
    cursor.execute("SELECT * FROM admin_logs ORDER BY timestamp DESC LIMIT 50")
    logs = [dict(row) for row in cursor.fetchall()]
    cursor.execute("SELECT COUNT(*) as total FROM shipments")
    shipment_count = cursor.fetchone()["total"]
    conn.close()
    return render_template("admin.html", users=users, logs=logs, shipment_count=shipment_count)


@app.route("/admin/users")
@login_required
def admin_users_api():
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT id, username, role, email, created_at FROM users")
    users = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return jsonify({"users": users})


@app.route("/admin/logs")
@login_required
def admin_logs_api():
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM admin_logs ORDER BY timestamp DESC LIMIT 100")
    logs = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return jsonify({"logs": logs})


# --- VULNERABILITY: Debug endpoint leaking config ---

@app.route("/debug")
def debug_info():
    return jsonify({
        "app": "Drakkar Shipping",
        "version": "1.2.3-dev",
        "flask_debug": app.debug,
        "database": DATABASE,
        "python_version": os.popen("python3 --version").read().strip(),
        "environment": dict(os.environ),
        "secret_key_length": len(app.secret_key),
        "registered_routes": [str(rule) for rule in app.url_map.iter_rules()],
        "server_time": datetime.now().isoformat(),
    })


@app.route("/api/status")
def api_status():
    return jsonify({
        "status": "operational",
        "service": "Drakkar Shipping API",
        "version": "1.2.3-dev",
        "uptime": "running",
        "debug": True,
    })


# --- Error handlers that still leak info in debug mode ---

@app.errorhandler(404)
def not_found(e):
    return render_template("404.html"), 404


if __name__ == "__main__":
    init_db()
    app.run(host="0.0.0.0", port=5000, debug=True)
