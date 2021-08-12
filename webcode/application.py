import os

from cs50 import SQL
from flask import Flask, flash, redirect, render_template, request, session
from flask_session import Session
from tempfile import mkdtemp
from werkzeug.exceptions import default_exceptions, HTTPException, InternalServerError
from werkzeug.security import check_password_hash, generate_password_hash
import requests
import json
import re
import urllib.parse
from functools import wraps


def apology(message, code=400):
    """Render message as an apology to user."""
    def escape(s):
        """
        Escape special characters.
        https://github.com/jacebrowning/memegen#special-characters
        """
        for old, new in [("-", "--"), (" ", "-"), ("_", "__"), ("?", "~q"),
                         ("%", "~p"), ("#", "~h"), ("/", "~s"), ("\"", "''")]:
            s = s.replace(old, new)
        return s
    return render_template("apology.html", top=code, bottom=escape(message)), code


def login_required(f):
    """
    Decorate routes to require login.
    https://flask.palletsprojects.com/en/1.1.x/patterns/viewdecorators/
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get("user_id") is None:
            flash("Simulator Requires Login")
            return render_template("login.html")
        return f(*args, **kwargs)
    return decorated_function



def usd(value):
    """Format value as USD."""
    return f"${value:,.2f}"

def lookup1(symbol):
    """Look up quote for symbol."""
    name = symbol.lower()
    
    counter = 0
    
    index = -1
        
    coins = requests.get("https://api.coingecko.com/api/v3/coins/markets?vs_currency=usd&order=market_cap_desc&per_page=80&page=1&sparkline=false&price_change_percentage=24h", headers = {"accept" : "application/json"})
    
    for coin in coins:
        if coins.json()[counter]['symbol'] == name or coins.json()[counter]['name'].lower() == name:
            index = counter
            break
        else:
            counter += 1
            
            if counter == 80:
                break
    
    if index == -1:
        return None
        
    return [coins.json()[index]['current_price'], coins.json()[index]['name'], coins.json()[index]['id']]


app = Flask(__name__)

# Ensure templates are auto-reloaded
app.config["TEMPLATES_AUTO_RELOAD"] = True


# Ensure responses aren't cached
@app.after_request
def after_request(response):
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response


# Custom filter
app.jinja_env.filters["usd"] = usd

# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_FILE_DIR"] = mkdtemp()
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Configure CS50 Library to use SQLite database
db = SQL("sqlite:////home/brandonpetersen/cryptoutlook/crypto.db")

    

@app.route("/")
def index():
    
    
    coin = requests.get("https://api.coingecko.com/api/v3/simple/price?ids=ethereum%2Cbitcoin%2Ctether%2Cdogecoin&vs_currencies=usd&include_market_cap=true&include_24hr_vol=true&include_24hr_change=true&include_last_updated_at=true", headers = {"accept" : "application/json"})
        
    bitprice = usd(coin.json()['bitcoin']['usd'])
    etherprice = usd(coin.json()['ethereum']['usd'])
    tetherprice = usd(coin.json()['tether']['usd'])
    dogeprice = usd(coin.json()['dogecoin']['usd'])
        
    bitcap = usd(coin.json()['bitcoin']['usd_market_cap'])
    ethercap = usd(coin.json()['ethereum']['usd_market_cap'])
    tethercap = usd(coin.json()['tether']['usd_market_cap'])
    dogecap = usd(coin.json()['dogecoin']['usd_market_cap'])
        
    bitvol = usd(coin.json()['bitcoin']['usd_24h_vol'])
    ethervol = usd(coin.json()['ethereum']['usd_24h_vol'])
    tethervol = usd(coin.json()['tether']['usd_24h_vol'])
    dogevol = usd(coin.json()['dogecoin']['usd_24h_vol'])
        
    bit24 = round(coin.json()['bitcoin']['usd_24h_change'], 2)
    ether24 = round(coin.json()['ethereum']['usd_24h_change'], 2)
    tether24 = round(coin.json()['tether']['usd_24h_change'], 2)
    doge24 = round(coin.json()['dogecoin']['usd_24h_change'], 2)
    
    event = requests.get("https://api.coingecko.com/api/v3/events", headers = {"accept" : "application/json"})
    
    events = event.json()
    
    
    return render_template("index.html", bitprice = bitprice, etherprice = etherprice, tetherprice = tetherprice, dogeprice = dogeprice, bitcap = bitcap, ethercap = ethercap, tethercap = tethercap,
    dogecap = dogecap, bitvol = bitvol, ethervol = ethervol, tethervol = tethervol, dogevol = dogevol, bit24 = bit24, ether24 = ether24, tether24 = tether24, doge24 = doge24, events = events)


@app.route("/trending")
def trending():
    
    var = lookup1("bitcoin")
    
    btc = var[0]
    
    trending1 = requests.get("https://api.coingecko.com/api/v3/search/trending", headers = {"accept" : "application/json"})
    trending = trending1.json()
    
    coins = trending['coins']
    
    return render_template("trending.html", coins = coins, btc = btc)
    

@app.route("/search",  methods=["GET", "POST"])
def search3():
    if request.method == "POST":
        if not request.form.get("symbol"):
            search1 = requests.get("https://api.coingecko.com/api/v3/coins/bitcoin/market_chart?vs_currency=usd&days=1", headers = {"accept" : "application/json"})
            search = search1.json()
            coindata = requests.get("https://api.coingecko.com/api/v3/coins/bitcoin?market_data=false&community_data=false&developer_data=false&sparkline=false", headers = {"accept" : "application/json"})
            coin = coindata.json()
            s1 = re.sub('<[^>]+>', '', coin['description']['en'])
            coin['description']['en'] = s1
            flash("Must Provide Coin Name or ID")
            return render_template("search.html", search = search, coin = coin)
        
        symbol = request.form.get("symbol")
        coin1 = lookup1(symbol)

        if coin1 is None:
            search1 = requests.get("https://api.coingecko.com/api/v3/coins/"+symbol.lower()+"/market_chart?vs_currency=usd&days="+request.form.get('Select Time Range'), headers = {"accept" : "application/json"})
            search = search1.json()
            coindata = requests.get("https://api.coingecko.com/api/v3/coins/"+symbol.lower()+"?market_data=false&community_data=false&developer_data=false&sparkline=false", headers = {"accept" : "application/json"})
            coin = coindata.json()
            if len(search) == 1:
                search1 = requests.get("https://api.coingecko.com/api/v3/coins/bitcoin/market_chart?vs_currency=usd&days=1", headers = {"accept" : "application/json"})
                search = search1.json()
                coindata = requests.get("https://api.coingecko.com/api/v3/coins/bitcoin?market_data=false&community_data=false&developer_data=false&sparkline=false", headers = {"accept" : "application/json"})
                coin = coindata.json()
                s1 = re.sub('<[^>]+>', '', coin['description']['en'])
                coin['description']['en'] = s1
                flash("Coin not found, please input valid coin ID or name of supported coin")
                return render_template("search.html", search = search, coin = coin)
            s1 = re.sub('<[^>]+>', '', coin['description']['en'])
            coin['description']['en'] = s1    
            return render_template("search.html", search = search, coin = coin)
        
        else:
            search1 = requests.get("https://api.coingecko.com/api/v3/coins/"+coin1[2]+"/market_chart?vs_currency=usd&days="+request.form.get('Select Time Range'), headers = {"accept" : "application/json"})
            search = search1.json()
            coindata = requests.get("https://api.coingecko.com/api/v3/coins/"+coin1[2]+"?market_data=false&community_data=false&developer_data=false&sparkline=false", headers = {"accept" : "application/json"})
            coin = coindata.json()
            s1 = re.sub('<[^>]+>', '', coin['description']['en'])
            coin['description']['en'] = s1
            return render_template("search.html", search = search, coin = coin)
    else:
        search1 = requests.get("https://api.coingecko.com/api/v3/coins/bitcoin/market_chart?vs_currency=usd&days=1", headers = {"accept" : "application/json"})
        search = search1.json()
        coindata = requests.get("https://api.coingecko.com/api/v3/coins/bitcoin?market_data=false&community_data=false&developer_data=false&sparkline=false", headers = {"accept" : "application/json"})
        coin = coindata.json()
        s1 = re.sub('<[^>]+>', '', coin['description']['en'])
        coin['description']['en'] = s1
        return render_template("search.html", search = search, coin = coin)
    
@app.route("/searchlink", defaults = {'coin': 'bitcoin'})
@app.route("/searchlink/<coin>") 
def searchlink(coin):
        
    coin1 = lookup1(coin)

    if coin1 is None:
        search1 = requests.get("https://api.coingecko.com/api/v3/coins/"+coin+"/market_chart?vs_currency=usd&days=1", headers = {"accept" : "application/json"})
        search = search1.json()
        coindata = requests.get("https://api.coingecko.com/api/v3/coins/"+coin+"?market_data=false&community_data=false&developer_data=false&sparkline=false", headers = {"accept" : "application/json"})
        coin = coindata.json()
        if len(search) == 1:
            search1 = requests.get("https://api.coingecko.com/api/v3/coins/bitcoin/market_chart?vs_currency=usd&days=1", headers = {"accept" : "application/json"})
            search = search1.json()
            coindata = requests.get("https://api.coingecko.com/api/v3/coins/bitcoin?market_data=false&community_data=false&developer_data=false&sparkline=false", headers = {"accept" : "application/json"})
            coin = coindata.json()
            s1 = re.sub('<[^>]+>', '', coin['description']['en'])
            coin['description']['en'] = s1
            flash("Coin not found, please input valid coin ID or name of supported coin")
            return render_template("search.html", search = search, coin = coin)
        s1 = re.sub('<[^>]+>', '', coin['description']['en'])
        coin['description']['en'] = s1    
        return render_template("search.html", search = search, coin = coin)
        
    else:
        search1 = requests.get("https://api.coingecko.com/api/v3/coins/"+coin1[2]+"/market_chart?vs_currency=usd&days=1", headers = {"accept" : "application/json"})
        search = search1.json()
        coindata = requests.get("https://api.coingecko.com/api/v3/coins/"+coin1[2]+"?market_data=false&community_data=false&developer_data=false&sparkline=false", headers = {"accept" : "application/json"})
        coin = coindata.json()
        s1 = re.sub('<[^>]+>', '', coin['description']['en'])
        coin['description']['en'] = s1
        return render_template("search.html", search = search, coin = coin)
    
    
@app.route("/portfolio")
@login_required
def portfolio():
    
    
    coin = requests.get("https://api.coingecko.com/api/v3/simple/price?ids=ethereum%2Cbitcoin%2Ctether%2Cdogecoin&vs_currencies=usd&include_market_cap=true&include_24hr_vol=true&include_24hr_change=true&include_last_updated_at=true", headers = {"accept" : "application/json"})
        
    bitprice = usd(coin.json()['bitcoin']['usd'])
    etherprice = usd(coin.json()['ethereum']['usd'])
    tetherprice = usd(coin.json()['tether']['usd'])
    dogeprice = usd(coin.json()['dogecoin']['usd'])
        
    bitcap = usd(coin.json()['bitcoin']['usd_market_cap'])
    ethercap = usd(coin.json()['ethereum']['usd_market_cap'])
    tethercap = usd(coin.json()['tether']['usd_market_cap'])
    dogecap = usd(coin.json()['dogecoin']['usd_market_cap'])
        
    bitvol = usd(coin.json()['bitcoin']['usd_24h_vol'])
    ethervol = usd(coin.json()['ethereum']['usd_24h_vol'])
    tethervol = usd(coin.json()['tether']['usd_24h_vol'])
    dogevol = usd(coin.json()['dogecoin']['usd_24h_vol'])
        
    bit24 = round(coin.json()['bitcoin']['usd_24h_change'], 2)
    ether24 = round(coin.json()['ethereum']['usd_24h_change'], 2)
    tether24 = round(coin.json()['tether']['usd_24h_change'], 2)
    doge24 = round(coin.json()['dogecoin']['usd_24h_change'], 2)
    
    
    total = db.execute("SELECT symbol, SUM(shares) as total FROM history WHERE user_id = ? GROUP BY symbol HAVING total > 0", session["user_id"])

    rows = db.execute("SELECT cash FROM users WHERE id = ?", session["user_id"])
    cash = rows[0]["cash"]

    coins = []

    fulltotal = 0
    

    for row in total:
        coin = lookup1(row["symbol"])
        coins.append({
            "name": coin[1],
            "shares": row["total"],
            "price": coin[0],
            "total": usd(coin[0] * row["total"])
        })
        fulltotal += coin[0] * row["total"]

    fulltotal += cash
    return render_template("portfolio.html", coins = coins, cash = usd(cash), fulltotal = usd(fulltotal), bitprice = bitprice, etherprice = etherprice, tetherprice = tetherprice, dogeprice = dogeprice, bitcap = bitcap, ethercap = ethercap, tethercap = tethercap,
    dogecap = dogecap, bitvol = bitvol, ethervol = ethervol, tethervol = tethervol, dogevol = dogevol, bit24 = bit24, ether24 = ether24, tether24 = tether24, doge24 = doge24)


@app.route("/buy", methods=["GET", "POST"])
@login_required
def buy():
    if request.method == "POST":
        if not request.form.get("symbol"):
            flash("Must Provide Symbol")
            return render_template("buy.html")
        elif not request.form.get("shares"):
            flash("Must Provide Number of Shares")
            return render_template("buy.html")
    

        symbol = request.form.get("symbol")
        coin = lookup1(symbol)

        if coin is None:
            flash("Coin Not Found")
            return render_template("buy.html")

        shares = float(request.form.get("shares"))
        price = coin[0]


        cash = db.execute("SELECT cash FROM users WHERE id = ?", session["user_id"])
        currentcash = cash[0]["cash"]
        if (shares * price) > currentcash:
            flash("Not Enough Cash")
            return render_template("buy.html")

        db.execute("UPDATE users SET cash = ? WHERE id = ?", currentcash - (shares * price), session["user_id"])
        db.execute("INSERT INTO history (user_id, symbol, shares, price) VALUES(?,?,?,?)", session["user_id"], coin[1], shares, price)

        flash("Bought!")
        return redirect("/portfolio")

    else:
        return render_template("buy.html")


@app.route("/history")
@login_required
def history():
    rows = db.execute("SELECT * FROM history WHERE user_id = ?", session["user_id"])
    
    for row in rows:
        row["price"] = usd(row["price"])
    
    return render_template("history.html", rows = rows)


@app.route("/login", methods=["GET", "POST"])
def login():
    """Log user in"""

    # Forget any user_id
    session.clear()

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # Ensure username was submitted
        if not request.form.get("username"):
            flash("Must Provide Username")
            return render_template("login.html")

        # Ensure password was submitted
        elif not request.form.get("password"):
            flash("Must Provide Password")
            return render_template("login.html")

        # Query database for username
        rows = db.execute("SELECT * FROM users WHERE username = ?", request.form.get("username"))

        # Ensure username exists and password is correct
        if len(rows) != 1 or not check_password_hash(rows[0]["hash"], request.form.get("password")):
            flash("Invalid Username and/or Password")
            return render_template("login.html")

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
    coin1 = None
    if request.method == "POST":
        if not request.form.get("symbol"):
            flash("Must Provide a Ticker Symbol")
            return render_template("quote.html", coin = coin1)
        symbol = request.form.get("symbol")
        coin2 = lookup1(symbol)
        if coin2 is None:
            flash("Coin Not Found, Simulator Only Supports the 80 Largest Coins")
            return render_template("quote.html", coin = coin1)
        
        coin = requests.get("https://api.coingecko.com/api/v3/coins/markets?vs_currency=usd&ids="+coin2[2]+"&order=market_cap_desc&per_page=80&page=1&sparkline=false&price_change_percentage=24h", headers = {"accept" : "application/json"})
        
        coin1 = coin.json()
        
        return render_template("quote.html", coin = coin1)
    else:
        return render_template("quote.html", coin = coin1)


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        if not request.form.get("username"):
            flash("Must Provide Username")
            return render_template("register.html")

        elif not request.form.get("password"):
            flash("Must Provide Password")
            return render_template("register.html")

        elif not request.form.get("confirmation"):
            flash("Must Confirm Password")
            return render_template("register.html")

        elif (request.form.get("password")) != (request.form.get("confirmation")):
            flash("Passwords Don't Match")
            return render_template("register.html")

        rows = db.execute("SELECT * FROM users WHERE username = ?", request.form.get("username"))

        if len(rows) != 0:
            flash("Username Taken")
            return render_template("register.html")

        idkey = db.execute("INSERT INTO users (username, hash) VALUES(:username, :hash)", username=request.form.get("username"), hash=generate_password_hash(request.form.get("password")))

        if idkey is None:
            return apology("Error with registration", 400)

        session["user_id"] = idkey

        flash("Registered!")
        return redirect("/")

    else:
        return render_template("register.html")


@app.route("/sell", methods=["GET", "POST"])
@login_required
def sell():
    if request.method == "POST":
        owned = db.execute("SELECT symbol FROM history WHERE user_id = ? GROUP BY symbol HAVING SUM(shares) > 0", session["user_id"])
        symbols = []
        for own in owned:
            symbols.append(own["symbol"])
        
        if not request.form.get("symbol"):
            flash("Must Provide Symbol")
            return render_template("sell.html", symbols = symbols)
        elif not request.form.get("shares"):
            flash("Must Provide Number of Shares")
            return render_template("sell.html", symbols = symbols)
    


        symbol = request.form.get("symbol")
        coin = lookup1(symbol)

        if coin is None:
            flash("Coin Not Found")
            return render_template("sell.html", symbols = symbols)

        rows =  db.execute("SELECT * FROM history WHERE user_id = :user_id AND symbol = :symbol", user_id= session["user_id"], symbol = coin[1])
        
        total = 0
        
        for row in rows:
            total += row["shares"]
        
        shares = float(request.form.get("shares"))
        price = coin[0]
        
        if shares > total:
            flash("Not Enough Shares Owned")
            return render_template("sell.html", symbols = symbols)

        cash = db.execute("SELECT cash FROM users WHERE id = ?", session["user_id"])
        currentcash = cash[0]["cash"]


        db.execute("UPDATE users SET cash = ? WHERE id = ?", currentcash + (shares * price), session["user_id"])
        db.execute("INSERT INTO history (user_id, symbol, shares, price) VALUES(?,?,?,?)", session["user_id"], symbol, -shares, price)

        flash("Sold!")
        return redirect("/portfolio")

    else:
        rows = db.execute("SELECT symbol FROM history WHERE user_id = ? GROUP BY symbol HAVING SUM(shares) > 0", session["user_id"])
        symbols = []
        for row in rows:
            symbols.append(row["symbol"])
        return render_template("sell.html", symbols = symbols)
        

@app.route("/changepass", methods=["GET", "POST"])
@login_required
def changepass():
    if request.method == "POST":

        if not request.form.get("newpass"):
            flash("Must Provide Password")
            return render_template("password.html")

        elif not request.form.get("confirmpass"):
            flash("Must Confirm Password")
            return render_template("password.html")

        elif (request.form.get("newpass")) != (request.form.get("confirmpass")):
            flash("Passwords Don't Match")
            return render_template("password.html")

        db.execute("UPDATE users SET hash = ? WHERE id = ?", generate_password_hash(request.form.get("newpass")), session["user_id"])
        
        flash("Reset Password!")
        return redirect("/")
    else:
        return render_template("password.html")

def errorhandler(e):
    """Handle error"""
    if not isinstance(e, HTTPException):
        e = InternalServerError()
    return apology(e.name, e.code)


# Listen for errors
for code in default_exceptions:
    app.errorhandler(code)(errorhandler)
