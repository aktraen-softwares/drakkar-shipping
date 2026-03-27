#!/usr/bin/env python3
"""
Drakkar Shipping — Internal Shipping Portal
Developer: Ragnar Sigurdsson <ragnar.sigurdsson@drakkar-shipping.is>
Last updated: 2026-03-15

WARNING: This file contains credentials. Do NOT commit to public repos.
TODO: Move secrets to environment variables before next audit.
"""

import os
import sqlite3
import hashlib
from flask import Flask, render_template, request, session, redirect, jsonify

app = Flask(__name__)

# ============================================================
# APPLICATION SECRETS — MOVE TO ENV VARS BEFORE PRODUCTION!
# ============================================================
app.secret_key = "drakkar-flask-secret-2026-xK9mW3pQ7vL"

# Database configuration
DATABASE_PATH = "/data/drakkar.db"
# Fallback for local dev: ./drakkar.db

# Admin credentials (created on first run)
ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = "DK!superadmin#2026"

# Auditor account (for external security reviews)
AUDIT_USERNAME = "audit"
AUDIT_PASSWORD = "DK!audit2026"

# Flask debug — DISABLE IN PRODUCTION
DEBUG_MODE = True

# Internal API key for service-to-service calls
INTERNAL_API_KEY = "dk-internal-api-9f8e7d6c5b4a"

# SMTP config for notifications
SMTP_HOST = "mail.drakkar-shipping.is"
SMTP_USER = "noreply@drakkar-shipping.is"
SMTP_PASS = "Dk$mail2026!"

# ============================================================

def get_db():
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    return conn

# ... (rest of application code)
# Routes: /, /services, /about, /contact, /track, /login, /client
# Admin routes: /admin/, /admin/users, /admin/logs
# Debug routes: /debug, /api/status

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=DEBUG_MODE)
