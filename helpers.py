import os
import requests
import urllib.parse
import requests
import json

from flask import redirect, render_template, request, session, flash
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
