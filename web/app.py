# -*- coding: utf-8 -*-
"""Web panel: channels management, event edit/delete with Telegram sync."""
from __future__ import annotations

import functools
import os
import sys
from pathlib import Path

from flask import Flask, flash, redirect, render_template, request, session, url_for
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
load_dotenv(ROOT / ".env")

from web.queries import (
    add_channel,
    delete_channel,
    get_channels,
    get_dashboard_counts,
    get_event_detail,
    get_events,
    get_messages,
    telegram_delete_message,
    telegram_edit_message,
    toggle_channel,
    update_event_text,
)

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


@app.route("/channels", methods=["GET", "POST"])
@login_required
def channels():
    if request.method == "POST":
        action = request.form.get("action")
        if action == "add":
            name = request.form.get("name", "")
            username = request.form.get("username", "")
            if add_channel(name, username):
                flash(f"Канал @{username.lstrip('@')} добавлен", "success")
            else:
                flash("Не удалось добавить канал", "error")
        elif action == "toggle":
            toggle_channel(int(request.form["channel_id"]))
            flash("Статус канала изменён", "success")
        elif action == "delete":
            delete_channel(int(request.form["channel_id"]))
            flash("Канал удалён", "success")
        return redirect(url_for("channels"))
    items = get_channels()
    return render_template("channels.html", channels=items)


@app.route("/events")
@login_required
def events():
    items = get_events(limit=100)
    return render_template("events.html", events=items)


@app.route("/events/<int:event_id>", methods=["GET", "POST"])
@login_required
def event_detail(event_id):
    if request.method == "POST":
        action = request.form.get("action")
        if action == "edit":
            new_text = request.form.get("text", "")
            update_event_text(event_id, new_text)
            if telegram_edit_message(event_id, new_text):
                flash("Сообщение обновлено и в Telegram", "success")
            else:
                flash("Текст сохранён, но Telegram не отредактирован (пост был с медиа или уже удалён)", "warning")
        elif action == "delete":
            if telegram_delete_message(event_id):
                flash("Пост удалён из Telegram", "success")
            else:
                flash("Не удалось удалить пост", "error")
        return redirect(url_for("event_detail", event_id=event_id))
    detail = get_event_detail(event_id)
    if not detail:
        flash("Событие не найдено", "error")
        return redirect(url_for("events"))
    return render_template("event_detail.html", e=detail)


@app.route("/messages")
@login_required
def messages():
    status = request.args.get("status")
    items = get_messages(limit=100, status=status)
    return render_template("messages.html", messages=items)


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=False)


@app.route("/health")
def health():
    return {"status": "ok"}
