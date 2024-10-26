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

    if request.method == "POST":
        if not request.form.get("username"):
            flash("Username missing")

        elif not request.form.get("password"):
            flash("Password missing")

        rows = cursor.execute("SELECT * FROM users WHERE username = ?", request.form.get("username"))

        if len(rows) != 1:
            flash("User not registered")
        elif not check_password_hash(rows[0]["password"], request.form.get("password")):
            flash(f"Invalid password for user {request.form.get("username")}")

        session["user_id"] = rows[0]["id"]
        return redirect("/")
    else:
        return render_template("login.html")
