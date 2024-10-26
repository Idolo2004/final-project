import os
import sqlite3
from flask import Flask, flash, redirect, render_template, request, session
from flask_session import Session
from werkzeug.security import check_password_hash, generate_password_hash

app = Flask(__name__)

database = "workouts.db"

app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)


@app.after_request
def after_request(response):
    """Ensure responses aren't cached"""
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response


@app.route("/")
def index():
    return render_template("layout.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    session.clear()
    conn = sqlite3.connect(database)
    cursor = conn.cursor()

    username = request.form.get("username")
    password = request.form.get("password")

    if request.method == "POST":
        if not username:
            flash("Username missing")

        if not password:
            flash("Password missing")

        cursor.execute("SELECT * FROM users WHERE username = ?", (username,))
        rows = cursor.fetchall()

        if IndexError:
            flash("User not registered")

        user = rows[0]
        if not check_password_hash(user["password"], password):
            flash(f"Invalid password for user {username}")

        session["user_id"] = user["id"]
        return redirect("/")
    else:
        return render_template("login.html")
