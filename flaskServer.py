from flask import Flask, url_for, render_template, request, redirect, session
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, EmailField
from wtforms.validators import DataRequired
import socket
from flask_httpauth import HTTPBasicAuth
from pymongo import MongoClient
import requests
from zeroconf import ServiceBrowser, Zeroconf
import threading
from serviceKeys import *
import yagmail
from datetime import datetime, timedelta
import yfinance
from newsapi import NewsApiClient

# Create a Flask object named app
app = Flask(__name__)

# Configure the app to be able to use sessions
app.secret_key = "testing"  # Change this to random string for more security

# MongoDB Connection (Default Port)
client = MongoClient('localhost', 27017)

# Set the database to the Credentials database
db = client.ECE4564_FinalProject

# Set the collection to the credentials collection
stock_coll = db.stock_portfolios

# Set the collection to the credentials collection
credentials = db.service_auth

# Create a HTTP Basic Authentication object named auth
auth = HTTPBasicAuth()

# Authenticate to email account for sending
yag = yagmail.SMTP('ece4564final@gmail.com', 'FinalProject!64')

# Initialize variables for data from LED Pi
LEDip = ''
LEDport = ''
LEDcolors = []

# Initialize variables for user email, stocks
userEmail = ''
stockTickers = []

# Initialize NewsAPI client
api = NewsApiClient(api_key=newsapi_key)

# Initialize timing variables
start_date_time = ''
hoursElapsed = 0
hoursPref = 0

# Define class for listening for zeroconf advertising
# Starter code taken from Zeroconf Github page - https://github.com/jstasiak/python-zeroconf
class Listener:
    def remove_service(self, zeroconf, type, name):
        print("Zeroconf: Service %s removed" % (name,))

    def update_service():
        pass

    def add_service(self, zeroconf, type, name):
        global LEDip
        global LEDport
        global LEDcolors

        info = zeroconf.get_service_info(type, name)

        if (info):

            print("Zeroconf: Service %s added, service info: %s" % (name, info))

            # Grab IP address and port from ServiceInfo object
            LEDip = socket.inet_ntoa(info.address)
            print("Zeroconf: IP address found: " + LEDip)
            LEDport = info.port
            print("Zeroconf: Port found: " + str(LEDport))

            # Grab list of colors from ServiceInfo object
            print("Zeroconf: Colors available: " + str(info.properties))
            LEDcolors = info.properties[b'Colors']
        
        else:
            print("Zeroconf: No service found")

            
# Run zeroconf listener to check for new services
def runZeroconf():
    zc = Zeroconf()
    listener = Listener()
    browser = ServiceBrowser(zc, "_http._tcp.local.", listener)
    print("Zeroconf: Initialized")

t1 = threading.Thread(target=runZeroconf)
t1.daemon = True
t1.start()

# Calculate number of hours elapsed
def get_delta(l, r):
    return abs(int((l-r).total_seconds())) / 3600

# Timer function to count hours elapsed
def checkDigest():
    global start_date_time
    global hoursElapsed
    global hoursPref
    global userEmail

    sent = 0

    while(True):
    
        end_date_time = datetime.now()

        # Increment hours elapsed, if an hour passed, reset email sent flag
        if (int(get_delta(start_date_time, end_date_time)) > hoursElapsed):
            hoursElapsed += 1
            sent = 0

        # Check if digest preference hours elapsed have been met
        if (((hoursElapsed % hoursPref) == 0) and (hoursPref != 0) and (sent == 0)):

            # Find user stocks and digest preference
            i_val = stock_coll.find_one({"user": userEmail})['initial_val']
            stocks = stock_coll.find_one({"user": userEmail})['stocks']
            digest_pref = stock_coll.find_one({"user": userEmail})['digest']

            # Add price to stock in db
            count = 0
            for stock in stocks:
                
                # Find price from ticker
                price = stockTickers[count].info['regularMarketPrice']

                # Update price in db
                if (len(stock) == 3):
                    stock[2] = price
                # Add price in db
                else:
                    stock.append(price)

                count += 1
                
            # Update db
            user_filter = {'user': userEmail}
            new_prefs = {"$set": {'initial_val': i_val, 'stocks': stocks, 'digest': digest_pref}}
            stock_coll.update_one(user_filter, new_prefs)

            # Create email body contents
            contents = ["Here is your stock digest:\n"]
            for stock in stocks:
                contents.append("Stock: " + stock[0] + " Shares owned: " + stock[1] + " Current price: " + stock[2] + "\n")

            # Add total gain/loss
            # TODO
                

            # Send digest email
            send_email(userEmail, digest_pref + " Stock Digest", contents)
            sent = 1

t2 = threading.Thread(target=checkDigest)
t2.daemon = True
t2.start()

# Function for sending an email to the user
# contents should be a list []
def send_email(address, subject, contents):
    yag.send(address, subject, contents)

# Callback function that verifies credentials by searching for them on the database
# @auth.verify_password
# def verify_password(username, password):
#     # Find an instance of this username and password pair in the database
#     user = col.find_one({'username': username, 'password': password})

#     # If the user is found then return the username, otherwise return nothing
#     if user:
#         return username
#     return None
  
# Error Handler function which gives message when login credentials fail
# @auth.error_handler
# def unauthorized():
#     return '401 - Unauthorized: Access is denied due to invalid credentials'

# Post commands for the LED
# @app.route('/LED', methods=['GET','POST'])
# @auth.login_required
# def led_command():

#     # Take in URL parameters
#     command = request.args.get('command')

#     color = command

#     # Send post request to LED
#     r = requests.post('http://'+ LEDip +':'+ str(LEDport) +'/LED?color='+ color)

#     return r.text

# This class specifies the structure for a standard login or account creation page
class epForm(FlaskForm):
    email = EmailField('email', validators=[DataRequired()])
    password = PasswordField('password', validators=[DataRequired()])


# This is the default app route, it checks for a user session and determines whether or not to go to the login page or
# to go to the user's dashboard
@app.route('/', methods=['POST', 'GET'])
def home():
    # If there is no user in a session, redirect to the login page
    if not session.get("email"):
        return redirect(url_for('login_redir'))

    # Otherwise go to the user's dashboard
    else:
        return redirect(url_for('dash_page'))


@app.route('/login', methods=['POST', 'GET'])
def login_redir():
    return redirect(url_for('login_page', message=" "))


# This is the login app route, it displays a login page with forms to fill out the user's email and password
@app.route('/login/<message>', methods=['POST', 'GET'])
def login_page(message):
    # If a user is already in a session then this page will be inaccessible
    if session.get("email"):
        return redirect(url_for('dash_page'))
    
    form = epForm()
    if request.method == 'POST':
        if form.is_submitted():
            email = form.email.data
            password = form.password.data

            user_found = credentials.find_one(({'user': email, 'password': password}))
            
            # if matched go to the user's dashboard
            if user_found:
                session["email"] = email    # Create the user's session
                return redirect(url_for('dash_page'))

            # If not matched, reload the page with an Invalid credentials message
            else:
                message = 'Invalid Credentials'
                return redirect(url_for('login_page', message=message))

    return render_template("login.html", message=message, form=form)


new_acc = False


@app.route('/create_acc', methods=['POST', 'GET'])
def c_acc_redir():
    return redirect(url_for('create_acc_page', message=" "))


# This is the account creation app route, it allows users to input new account credentials to the database
@app.route('/create_acc/<message>', methods=['POST', 'GET'])
def create_acc_page(message):

    # If a user is already in a session then this page will be inaccessible
    if session.get("email"):
        return redirect(url_for('dash_page'))

    form = epForm()
    if request.method == 'POST':
        if form.is_submitted():
            email = form.email.data
            password = form.password.data
            if len(password) == 0:
                message = 'Please input a password'
                return redirect(url_for('create_acc_page', message=message))
        
        # Check the email against the list of known users
        user_found = credentials.find_one(({'user': email}))

        # if email matches an existing account, then reload the page with an error message
        if user_found:
            message = 'Email already in use'
            return redirect(url_for('create_acc_page', message=message))

        # if email doesn't match any known emails, continue to preferences page
        else:
            # Establish this user's session
            session["email"] = email

            # Insert new account info into database
            new_info = {'user': email, 'password': password}
            credentials.insert_one(new_info)

            # if submit is pressed and account does not exist,
            # set new_acc to true which is set to false when dashboard is accessed
            # Since the user doesn't exist, go through first time set up
            new_acc = True
            return redirect(url_for('prefs_page'))

    return render_template("create_acc.html", message=message)


# This is the account preferences page, it allows the user to set their preferences for time and number of companies
@app.route('/prefs', methods=['POST', 'GET'])
def prefs_page():

    # Access global stockTicker array
    global stockTickers
    global start_date_time
    global hoursPref
    global userEmail

    # Can only be accessible if a user is in session
    if not session.get("email"):
        return redirect(url_for('login_page'))

    if request.method == 'POST':
        stocks = []
        for i,(k,v) in enumerate(request.form.items()):
            if k != "Submit" and k != "hidden_field":
                if i%2 == 1:
                    stocks.append([v])
                else:
                    stocks[len(stocks)-1].append(v)
        digest_pref = request.form['hidden_field']
        print(digest_pref)
        print(stocks)

        # store in db here
        # If first time set up just add to database, otherwise need to update user preferences
        # Search for user in stock portfolios collection
        email = session["email"]
        userEmail = email
        user_found = stock_coll.find_one(({'user': email}))


        if user_found:
            # Update preferences
            user_filter = {'user': email}
            new_prefs = {"$set": {'initial_val': 0, 'stocks': stocks, 'digest': digest_pref}}
            stock_coll.update_one(user_filter, new_prefs)

        else:
            # Add a new preference
            stock_coll.insert_one({'initial_val': 0, 'user': email, 'stocks': stocks, 'digest': digest_pref})

        # Update stockTickers and stockPrices arrays with user's stocks
        start_date_time = datetime.now()

        # Update number of hours for digest preferences
        if (digest_pref == "hourly"):
            hoursPref = 1
        elif (digest_pref == "daily"):
            hoursPref = 24
        elif (digest_pref == "weekly"):
            hoursPref = 168
        else:
            hoursPref = 0

        stockTickers.clear()
        for stock in stock_coll.find_one({"user":email})['stocks']:

            # Create stock ticker
            stockTick = yfinance.Ticker(stock[0])
            stockTickers.append(stockTick)
        
        print(stockTickers)
        print(stock_coll.find_one({"user": session["email"]}))
        # Add price to stock in db
        count = 0
        stock_tmp = stocks
        # for stock in stocks:
        total_value = 0
        print(stock_tmp)
        print(len(stocks))
        for i in range(len(stocks)):
            print(stocks[i])
            # Find price from ticker
            price = stockTickers[i].info['regularMarketPrice']

            # Update price in db
            if (len(stocks[i]) == 3):
                stock_tmp[i][2] = price
            # Add price in db
            else:
                stock_tmp[i].append(price)
                print("sdf",stock_tmp[i][2],stock_tmp[i][1])
                total_value += float(stock_tmp[i][2])*float(stock_tmp[i][1])

            # count += 1
                
        # Update db
        user_filter = {'user': userEmail}
        new_prefs = {"$set": {'initial_val': total_value, 'stocks': stock_tmp, 'digest': digest_pref}}
        stock_coll.update_one(user_filter, new_prefs)

        return redirect(url_for('dash_page'))
    return render_template("prefs.html")


@app.route('/dash', methods=['POST', 'GET'])
def dash_redir():
    return redirect(url_for('dash_page', status=" "))

@app.route('/dash/<status>', methods=['GET'])
def dash_page(status):
    # Can only be accessible if a user is in session
    # global stockTickers
    # stockTickers.clear()
    stockTickers = []
    for stock in stock_coll.find_one({"user": session["email"]})['stocks']:
        print(stock[0])
        # Create stock ticker
        stockTick = yfinance.Ticker(stock[0])
        stockTickers.append(stockTick)

    if status == "refresh":
        stocks = stock_coll.find_one({"user": session["email"]})['stocks']
        stock_tmp = stocks
        # for stock in stocks:
        print(stock_tmp)
        print(len(stocks))
        print(len(stockTickers))
        for i in range(len(stocks)):
            print(stocks[i])
            # Find price from ticker
            price = stockTickers[i].info['regularMarketPrice']

            # Update price in db
            if (len(stocks[i]) == 3):
                stock_tmp[i][2] = price
            # Add price in db
            else:
                stock_tmp[i].append(price)
                print("sdf",stock_tmp[i][2],stock_tmp[i][1])

        user_filter = {'user': userEmail}
        new_prefs = {"$set": {'initial_val': stock_coll.find_one({"user": session["email"]})['initial_val'], 'stocks': stock_tmp, 'digest': stock_coll.find_one({"user": session["email"]})['digest'] }}

        stock_coll.update_one(user_filter, new_prefs)

    if not session.get("email"):
        return redirect(url_for('login_page'))
    print(stock_coll.find_one({"user": session["email"]}))
    stocks = stock_coll.find_one({"user": session["email"]})['stocks']
    initial_value = stock_coll.find_one({"user": session["email"]})['initial_val']
    articles = []
    # print(stock_coll.find_one({"user": session["email"]})['stocks'])
    for i in stocks:
        query = i[0]+" stock"
        news = api.get_everything(q=query,sort_by="relevancy")['articles']
        # print(news)
        articles.append([news[0]["title"], news[0]["url"]])
        articles.append([news[1]["title"], news[1]["url"]])
    print(articles)
    return render_template("dashboard.html", stocks=stocks, i_val=initial_value, articles=articles)

# This is the log out route, it ends the user's session
@app.route("/logout")
def logout():
    # End the user's session and redirect to home page
    session["email"] = None
    return redirect(url_for('home'))


# Run the application when service is started
if __name__ == '__main__':
    app.run(debug=True)
