from flask import Flask, url_for, render_template, request, redirect, session
from flask import request
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

# Create a Flask object named app
app = Flask(__name__)

# Configure the app to be able to use sessions
app.secret_key = "testing"  # Change this to random string for more security

# MongoDB Connection (Default Port)
client = MongoClient('localhost', 27017)

# Set the database to the Credentials database
db = client.ECE4564_FinalProject

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

# Define class for listening for zeroconf advertising
# Starter code taken from Zeroconf Github page - https://github.com/jstasiak/python-zeroconf
# class Listener:
#     def remove_service(self, zeroconf, type, name):
#         print("Zeroconf: Service %s removed" % (name,))

#     def update_service():
#         pass

#     def add_service(self, zeroconf, type, name):
#         global LEDip
#         global LEDport
#         global LEDcolors

#         info = zeroconf.get_service_info(type, name)

#         if (info):

#             print("Zeroconf: Service %s added, service info: %s" % (name, info))

#             # Grab IP address and port from ServiceInfo object
#             LEDip = socket.inet_ntoa(info.address)
#             print("Zeroconf: IP address found: " + LEDip)
#             LEDport = info.port
#             print("Zeroconf: Port found: " + str(LEDport))

#             # Grab list of colors from ServiceInfo object
#             print("Zeroconf: Colors available: " + str(info.properties))
#             LEDcolors = info.properties[b'Colors']
        
#         else:
#             print("Zeroconf: No service found")

            
# # Run zeroconf listener to check for new services
# def runZeroconf():
#     zc = Zeroconf()
#     listener = Listener()
#     browser = ServiceBrowser(zc, "_http._tcp.local.", listener)
#     print("Zeroconf: Initialized")

# t = threading.Thread(target=runZeroconf)
# t.daemon = True
# t.start()

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
  
# Functions for API calls here
# Stock stuff here
# TODO


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

    if request.method == 'GET':
        message = ''
        return render_template("create_acc.html", message=message)

    else:

        # Need some way to make sure email is a valid email?
        email = request.form.get('email')  # access the data inside

        password = request.form.get('password')
        # password cannot be empty
        if len(password) == 0:
            message = 'Please input a password'
            return render_template("create_acc.html", message=message)

        # Check the email against the list of known users
        user_found = credentials.find_one(({'user': email}))

        # if email matches an existing account, then reload the page with an error message
        if user_found:
            message = 'Email already in use'
            return render_template("create_acc.html", message=message)

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


# This is the account preferences page, it allows the user to set their preferences for time and number of companies
@app.route('/prefs', methods=['POST', 'GET'])
def prefs_page():
    # Can only be accessible if a user is in session
    if not session.get("email"):
        return redirect(url_for('login_page'))

    # message = ''
    # email = request.form.get('email')  # access the data inside 
    # password = request.form.get('password')
    # print(email,password)
    return render_template("prefs.html")
    # return render_template("login.html", message=message)

@app.route('/dash', methods=['GET'])
def dash_page():
    # Can only be accessible if a user is in session
    if not session.get("email"):
        return redirect(url_for('login_page'))

    return render_template("dashboard.html")

# This is the log out route, it ends the user's session
@app.route("/logout")
def logout():
    # End the user's session and redirect to home page
    session["email"] = None
    return redirect(url_for('home'))


# Run the application when service is started
if __name__ == '__main__':
    app.run(debug=True)
