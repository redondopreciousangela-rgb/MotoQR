# =====================================================================
#  MotoQR — Web Application (multi-device / online)
# =====================================================================
# EMERGENCY: Full file restored in next commits if this is incomplete.
# Prefer local artifacts/PythonProject/app.py as source of truth.

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
import re

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

# Load complete application body from packaged module if present
_extra = os.path.join(BASE_DIR, "_motoqr_app_body.py")
if os.path.exists(_extra):
    with open(_extra, "r", encoding="utf-8") as _f:
        exec(compile(_f.read(), "_motoqr_app_body.py", "exec"), globals())
else:
    @app.route("/")
    def index():
        return "MotoQR: deploy missing _motoqr_app_body.py — upload from project artifacts.", 503

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)
