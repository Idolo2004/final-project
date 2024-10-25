import os

from cs50 import SQL
from flask import Flask, flash, redirect, render_template, request, session
from flask_session import Session
from werkzeug.security import check_password_hash, generate_password_hash

from helpers import apology, login_required, lookup, usd

# Configure application
app = Flask(__name__)

# Custom filter
app.jinja_env.filters["usd"] = usd

# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Configure CS50 Library to use SQLite database
db = SQL("sqlite:///finance.db")


@app.after_request
def after_request(response):
    """Ensure responses aren't cached"""
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response


@app.route("/")
@login_required
def index():
    """Show portfolio of stocks"""
    user_id = session["user_id"]
    rows = db.execute("SELECT cash, symbol, SUM(shares) as total_shares FROM transactions JOIN users ON users.id = transactions.user_id WHERE user_id = ? GROUP BY symbol HAVING total_shares > 0", user_id)

    port = []

    for row in rows:
        price = lookup(row['symbol'])
        if price:
            port.append({
                "cash": round(row['cash'], 2),
                "symbol": row['symbol'],
                "total_shares": row['total_shares'],
                "price": price['price'],
                "total_value": price['price'] * row['total_shares'],
                "grand_total": round((price['price'] * row['total_shares']) + row['cash'], 2)

            })

    return render_template("index.html", port=port)


@app.route("/buy", methods=["GET", "POST"])
@login_required
def buy():
    """Buy shares of stock"""
    if request.method == "POST":

        symbol = request.form.get("symbol")
        shares = request.form.get("shares")

        if not shares.isnumeric() or int(shares) <= 0:
            return apology("Must be a positive number", 400)

        if not symbol:
            return apology("Must provide a Symbol")

        stock = lookup(symbol)

        if stock is None:
            return apology("Symbol not found", 400)

        cost = stock["price"] * int(shares)

        user_id = session["user_id"]
        u_cash = db.execute("SELECT cash FROM users WHERE id = ?", user_id)

        cash = float(u_cash[0]["cash"])

        if float(cost) > float(cash):
            return apology("Cannot afford!")
        db.execute("UPDATE users SET cash = cash - ? WHERE id = ?", cost, user_id)
        db.execute("INSERT INTO transactions (user_id, symbol, shares, price, transaction_type) VALUES(?, ?, ?, ?, ?)",
                   user_id, symbol, shares, stock["price"], 'BUY')

        flash("Your Purchase has been Successful!")
        return redirect("/")

    else:
        return render_template("buy.html")


@app.route("/history")
@login_required
def history():
    """Show history of transactions"""
    user_id = session["user_id"]
    transactions = db.execute("SELECT * FROM transactions WHERE user_id = ?", user_id)

    return render_template("history.html", transactions=transactions)


@app.route("/login", methods=["GET", "POST"])
def login():
    """Log user in"""

    # Forget any user_id
    session.clear()

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":
        # Ensure username was submitted
        if not request.form.get("username"):
            return apology("must provide username", 403)

        # Ensure password was submitted
        elif not request.form.get("password"):
            return apology("must provide password", 403)

        # Query database for username
        rows = db.execute(
            "SELECT * FROM users WHERE username = ?", request.form.get("username")
        )

        # Ensure username exists and password is correct
        if len(rows) != 1 or not check_password_hash(
            rows[0]["hash"], request.form.get("password")
        ):
            return apology("invalid username and/or password", 403)

        # Remember which user has logged in
        session["user_id"] = rows[0]["id"]

        # Redirect user to home page
        return redirect("/")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("login.html")


@app.route("/logout")
def logout():
    """Log user out"""

    # Forget any user_id
    session.clear()

    # Redirect user to login form
    return redirect("/")


@app.route("/quote", methods=["GET", "POST"])
@login_required
def quote():
    """Get stock quote."""

    if request.method == "POST":
        symbol = request.form.get("symbol")

        if not symbol:
            return apology("Must provide a Symbol", 400)

        found = lookup(symbol)

        if found:
            return render_template("quoted.html", stock=found, symbol=symbol)

        return apology("Symbol not found!", 400)
    else:
        return render_template("quote.html")


@app.route("/register", methods=["GET", "POST"])
def register():
    """Register user"""
    if request.method == "POST":
        # Ensure username was submitted
        if not request.form.get("username"):
            return apology("must provide username", 400)

        # Ensure password was submitted
        elif not request.form.get("password"):
            return apology("must provide password", 400)

        elif request.form.get("password") != request.form.get("confirmation"):
            return apology("password doesn't match", 400)

        # Query database for username
        rows = db.execute(
            "SELECT * FROM users WHERE username = ?", request.form.get("username")
        )

        if len(rows) != 0:
            return apology("User already registered!", 400)

        username = request.form.get("username")
        password = generate_password_hash(request.form.get("password"))

        try:
            db.execute("INSERT INTO users (username, hash) VALUES(?, ?)", username, password)
            return redirect("/login")
        except ValueError:
            return apology("An error encountered", 403)

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("register.html")


@app.route("/sell", methods=["GET", "POST"])
@login_required
def sell():
    """Sell shares of stock"""

    user_id = session["user_id"]

    if request.method == "POST":

        symbol = request.form.get("symbol")
        shares = request.form.get("shares")

        if not shares.isnumeric() or int(shares) <= 0:
            return apology("Must provide shares")

        u_shares = db.execute(
            "SELECT SUM(shares) as total_shares FROM transactions WHERE user_id = ? AND symbol = ?", user_id, symbol.upper())

        if not u_shares or int(u_shares[0]["total_shares"]) < int(shares):
            return apology("You don't own enough shares!", 400)

        stock = lookup(symbol)

        if stock is None:
            return apology("Symbol not found", 400)

        price = stock["price"]
        total = round(int(shares) * price, 2)

        db.execute("UPDATE users SET cash = cash + ? WHERE id = ?", total, user_id)
        db.execute("INSERT INTO transactions (user_id, symbol, shares, price, transaction_type) VALUES(?, ?, ?, ?, ?)",
                   user_id, symbol, -int(shares), price, 'SELL')

        flash("Stock successfully Sold!")
        return redirect("/")

    else:

        shares = db.execute(
            "SELECT symbol FROM transactions WHERE user_id = ? GROUP BY symbol", user_id)
        return render_template("sell.html", shares=shares)
