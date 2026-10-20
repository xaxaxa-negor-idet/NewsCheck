# -*- coding: utf-8 -*-
"""Web panel: SPEC 14 — admin interface with auth."""
from __future__ import annotations

import functools
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from flask import Flask, redirect, render_template, request, session, url_for
from dotenv import load_dotenv

from web.queries import get_dashboard_counts, get_events, get_messages

ROOT = Path(__file__).resolve().parent.parent
load_dotenv(ROOT / ".env")

app = Flask(__name__)
app.secret_key = os.getenv("WEB_SECRET_KEY", "dev-secret-change-me")

USERNAME = os.getenv("WEB_USERNAME", "admin")
PASSWORD = os.getenv("WEB_PASSWORD", "admin")


def login_required(view):
    @functools.wraps(view)
    def wrapped(*args, **kwargs):
        if "user" not in session:
            return redirect(url_for("login"))
        return view(*args, **kwargs)
    return wrapped


@app.route("/login", methods=["GET", "POST"])
def login():
    error = None
    if request.method == "POST":
        if request.form["username"] == USERNAME and request.form["password"] == PASSWORD:
            session["user"] = USERNAME
            return redirect(url_for("dashboard"))
        error = "Неверный логин или пароль"
    return render_template("login.html", error=error)


@app.route("/logout")
def logout():
    session.pop("user", None)
    return redirect(url_for("login"))


@app.route("/")
@login_required
def dashboard():
    counts = get_dashboard_counts()
    return render_template("dashboard.html", counts=counts)


@app.route("/events")
@login_required
def events():
    items = get_events(limit=100)
    return render_template("events.html", events=items)


@app.route("/messages")
@login_required
def messages():
    status = request.args.get("status")
    items = get_messages(limit=100, status=status)
    return render_template("messages.html", messages=items, current_filter=status)


@app.route("/health")
def health():
    return {"status": "ok"}


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=False)
