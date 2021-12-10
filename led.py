from flask import Flask
from flask import request
from zeroconf import ServiceInfo, Zeroconf
import socket
import RPi.GPIO as GPIO

# Create a Flask object named app
app = Flask(__name__)

# Initialize LEDs
GPIO.setmode(GPIO.BCM)
r = 17
g = 27
b = 22
GPIO.setwarnings(False)
GPIO.setup(r, GPIO.OUT)
GPIO.setup(g, GPIO.OUT)
GPIO.setup(b, GPIO.OUT)
rLED = GPIO.PWM(r, 50)
gLED = GPIO.PWM(g, 50)
bLED = GPIO.PWM(b, 50)
ledColor = 'off'

# Initialize zeroconf object
zc = Zeroconf()

# Broadcast list of IP address, port, supported LED colors
desc = {'Colors': ['red', 'green']}

hostname = socket.gethostname()
local_ip = socket.gethostbyname(hostname + ".local.")

# Initialize ServiceInfo for zeroconf service
zcInfo = ServiceInfo("_http._tcp.local.",
                    "led rpi._http._tcp.local.",
                    address=socket.inet_aton(local_ip),
                    port=5000,
                    properties=desc, 
                    server="rpi1.local.",
                    )

try:
    print("Registration of zeroconf service, Ctrl+C to exit...")
    zc.register_service(zcInfo)
except:
    print("Error while registering zeroconf service.")

# Interpret LED command
def updateLED(color):

    

    if (color == "red"):
        rLED.start(100)
        gLED.stop()
        bLED.stop()

    elif (color == "green"):
        rLED.stop()
        gLED.start(100)
        bLED.stop()

    else:
        rLED.stop()
        gLED.stop()
        bLED.stop()
    
    pass

# Respond to GET/POST request for changing LED status and color
@app.route('/LED', methods=['GET','POST'])
def update_info():

    global ledColor

    # Get led color argument from HTTP request
    ledColor = request.args.get('color')

    updateLED(ledColor)

    returnStr = 'color='+ledColor + '\n'

    return returnStr 

# Run the application when service is started
if __name__ == '__main__':
    app.run(host="0.0.0.0")
