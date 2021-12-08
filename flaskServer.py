from flask import Flask, render_template
from flask import request
import socket
from flask_httpauth import HTTPBasicAuth
from pymongo import MongoClient
import requests
from zeroconf import ServiceBrowser, Zeroconf
import threading
from serviceKeys import *

# Create a Flask object named app
app = Flask(__name__)

# MongoDB Connection (Default Port)
client = MongoClient('localhost', 27017)

# Set the database to the Credentials database
db = client.ECE4564_FinalProject

# Set the collection to the credentials collection
col = db.service_auth

# Create a HTTP Basic Authentication object named auth
auth = HTTPBasicAuth()

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
#             LEDip = socket.inet_ntoa(info.addresses[0])
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

@app.route('/login', methods=['POST', 'GET'])
def login_page():
    message = ''
    email = request.form.get('email')  # access the data inside 
    password = request.form.get('password')
    print(email,password)
    
    #implement some authentication with the db and if not match,
    #message="Invalid credentials"
    #if match go to dashboard
    return render_template("login.html", message=message)

new_acc = False

@app.route('/create_acc', methods=['POST', 'GET'])
def create_acc_page():

    # if submit is pressed and account does not exist, 
    # set new_acc to true which is set to false when dashboard is accessed


    # message = ''
    # email = request.form.get('email')  # access the data inside 
    # password = request.form.get('password')
    # print(email,password)

    #if email matches an existing account, 
    #message="Email already in use"
    #if not continue to prefs
    return render_template("create_acc.html")
    # return render_template("login.html", message=message)

@app.route('/prefs', methods=['POST', 'GET'])
def prefs_page():
    # message = ''
    # email = request.form.get('email')  # access the data inside 
    # password = request.form.get('password')
    # print(email,password)
    return render_template("prefs.html")
    # return render_template("login.html", message=message)

# Run the application when service is started
if __name__ == '__main__':
    app.run(debug=True)
