#!/usr/bin/python

############################# CONFIG ########################################################

# Display parameters
DISPLAY_ADDRESS = 0x3C
RST = None
PADDING = 2
REFRESH_INTERVAL = 2
DEFAULT_MODE = 3
WAIT_FOR_MQTT = False

# MQTT Parameters
MQTT_HOST = "localhost"
MQTT_PORT = 1883
MQTT_KEEP_ALIVE = 60
MQTT_BIND_ADDRESS = ""
MQTT_USER = None
MQTT_PWD = None
DEFAULT_QOS = 0
LAST_WILL_TOPIC = "oled/status"
LAST_WILL_PAYLOAD = "0"
MODE_TOPIC = "oled/set"
STATE_TOPIC = "oled/state"

# Network interfaces
WIFI = 'wlan0'
ETH = 'eth0'

# Display Modes 
modes = ['Turn off', 'Wifi', 'Ethernet', 'Clock', 'Load', 'Disk usage', 'CPU Temp', 'RAM'];

############################ END OF CONFIG ###################################################


# Library import
import time
import sys
import Adafruit_SSD1306
import subprocess
from PIL import Image
from PIL import ImageDraw
from PIL import ImageFont
from datetime import datetime
import netifaces as ni
import paho.mqtt.client as mqtt


# Global var
mqtt_connection = False
mode = DEFAULT_MODE
first_run = True


########################### Initialize display ################################################## 

disp = Adafruit_SSD1306.SSD1306_128_64(rst=RST, i2c_address=DISPLAY_ADDRESS)
disp.begin()

# Clear display.
disp.clear()
disp.display()

# Cursor positioning
width = disp.width
height = disp.height
x = PADDING
top = PADDING
bottom = height-PADDING

# Create blank image for drawing.
# Make sure to create image with mode '1' for 1-bit color.
image = Image.new('1', (width, height))
draw = ImageDraw.Draw(image)

# Draw a black filled box to clear the image.
draw.rectangle((0,0,width,height), outline=0, fill=0)

# Load fonts and images.
font = ImageFont.truetype('/home/homeassistant/oled/Montserrat-Regular.ttf', 12)
font_text_big = ImageFont.truetype('/home/homeassistant/oled/Montserrat-Medium.ttf', 19)
font_text_small = ImageFont.truetype('/home/homeassistant/oled/Montserrat-Light.ttf', 12)
sys_icons = ImageFont.truetype('/home/homeassistant/oled/fontawesome-webfont.ttf', 16)
ethernet_icon = ImageFont.truetype('/home/homeassistant/oled/ethernet.ttf', 36)
sys_icons_big = ImageFont.truetype('/home/homeassistant/oled/fontawesome-webfont.ttf', 36)
font_text_clock = ImageFont.truetype('/home/homeassistant/oled/Montserrat-Medium.ttf', 36)

################################ MQTT CONNECTION ############################################

# Callback function for paho_mqtt connection
def on_connect(client, userdata, flags, rc):
	global mqtt_connection
	if rc == 0: 
		mqtt_connection = True  
		# Subscribe the mode topic
		mqttc.subscribe(MODE_TOPIC, DEFAULT_QOS) 
		# Set the status to 1
		mqttc.publish(LAST_WILL_TOPIC, "1", DEFAULT_QOS, False)
            
	else:
		mqtt_connection = False 

# Callback function for paho_mqtt disconnection
def on_disconnect(client, userdata, rc):
	global mqtt_connection
	if rc != 0:
		client.loop_stop()
		mqtt_connection = False

# Callback function for on message
def on_message(client, userdata, message):
	global MODE_TOPIC
	global modes
	global mode
	global first_run
	if message.topic == MODE_TOPIC:
		if message.payload in modes:
			mode = modes.index(message.payload)
			first_run = True
		else:
			mode = DEFAULT_MODE
	

mqttc = mqtt.Client("oled")
# Set user and pass
mqttc.username_pw_set(MQTT_USER, MQTT_PWD)
# Set the callback functios
mqttc.on_connect = on_connect  
mqttc.on_message = on_message  
mqttc.on_disconnect = on_disconnect
# Set the last will message 
mqttc.will_set(LAST_WILL_TOPIC, LAST_WILL_PAYLOAD, DEFAULT_QOS, False)
# Connect
mqttc.connect_async(MQTT_HOST, port = MQTT_PORT, keepalive = MQTT_KEEP_ALIVE, bind_address = MQTT_BIND_ADDRESS)
# Start the loop
mqttc.loop_start()
# Waiting for MQTT Connection
if WAIT_FOR_MQTT:
	while not mqtt_connection:
		# Draw a black filled box to clear the image.
		draw.rectangle((0,0,width,height), outline=0, fill=0)
		# Draw text for Header
		draw.text((x, top), "Waiting for",  font=font, fill=255)
		draw.text((x, top+19), "MQTT",  font=font_text_big, fill=255)
		draw.text((x, top+46), "Connection",  font=font, fill=255)
		# Display
		disp.image(image)
		disp.display()
		time.sleep(REFRESH_INTERVAL)
		disp.clear()
		disp.display()

################################# MAIN LOOP #############################################

while True:
	# Mode = Off
	if mode == 0:
		# Turn off the display if is the first iteraction in Off mode
		if first_run:
			disp.clear()
			disp.display()
			if first_run and mqtt_connection:
				mqttc.publish(STATE_TOPIC, modes[mode], DEFAULT_QOS, False)
			# Disable first_run
			first_run = False

	# Mode = Wifi
	elif mode == 1:
		# Retrieve network interface IPV4 address
		if WIFI in ni.interfaces():
			if ni.AF_INET in ni.ifaddresses(WIFI):
				wifi_ip = ni.ifaddresses(WIFI)[ni.AF_INET][0]['addr']
			else:
				wifi_ip = "No Conn."
		else:
			wifi_ip = "Not found"
		# Draw a black filled box to clear the image.
		draw.rectangle((0,0,width,height), outline=0, fill=0)
		# Draw text and icons for wifi
		draw.text((x+42, top), unichr(61931), font=sys_icons_big, fill=255)
		draw.text((x+2, top+42), wifi_ip,  font=font_text_big, fill=255)
		# Display
		disp.image(image)
		disp.display()
		# Publish the state to MQTT
		if first_run and mqtt_connection:
				mqttc.publish(STATE_TOPIC, modes[mode], DEFAULT_QOS, False)
		# Disable first_run
		first_run = False

	# Mode = Ethernet
	elif mode == 2:
		# Retrieve network interface IPV4 address
		if ETH in ni.interfaces():
			if ni.AF_INET in ni.ifaddresses(ETH):	
				eth_ip = ni.ifaddresses(ETH)[ni.AF_INET][0]['addr']
			else:
				eth_ip = "No Conn."
		else:
			eth_ip = "Not found"
		# Draw a black filled box to clear the image.
		draw.rectangle((0,0,width,height), outline=0, fill=0)
		# Draw text and icons for ethernet
		draw.text((x+42, top), "1", font=ethernet_icon, fill=255)
		draw.text((x+2, top+42), eth_ip,  font=font_text_big, fill=255)
		# Display
		disp.image(image)
		disp.display()
		# Publish the state to MQTT
		if first_run and mqtt_connection:
				mqttc.publish(STATE_TOPIC, modes[mode], DEFAULT_QOS, False)
		# Disable first_run
		first_run = False

	# Mode = Clock
	elif mode == 3:
		# Draw a black filled box to clear the image.
    		draw.rectangle((0,0,width,height), outline=0, fill=0)
		# Current time	
		now = datetime.now()
		hour = now.strftime("%H : %M")
		# Draw Text
		draw.text((x+10, top+12), hour,  font=font_text_clock, fill=255)
		# Display
		disp.image(image)
		disp.display()
		# Publish the state to MQTT
		if first_run and mqtt_connection:
				mqttc.publish(STATE_TOPIC, modes[mode], DEFAULT_QOS, False)
		# Disable first_run
		first_run = False
		
	# Mode = Load
	elif mode == 4:
		# Draw a black filled box to clear the image.
    		draw.rectangle((0,0,width,height), outline=0, fill=0)
		# Retrieve system info
		cmd = "top -bn1 | grep load | awk '{printf \"%.2f\", $(NF-2)}'"
    		CPU = subprocess.check_output(cmd, shell = True )
    		# Draw icons
    		draw.text((x, top+25), unichr(62171), font=sys_icons_big, fill=255)
		# Draw text
		draw.text((x+36, top), "LOAD",  font=font_text_big, fill=255)
		draw.text((x+36, top+25), str(CPU), font=font_text_clock, fill=255)
		# Display
		disp.image(image)
		disp.display()
		# Publish the state to MQTT
		if first_run and mqtt_connection:
				mqttc.publish(STATE_TOPIC, modes[mode], DEFAULT_QOS, False)
		# Disable first_run
		first_run = False

	# Mode = Disk usage
	elif mode == 5:
		# Draw a black filled box to clear the image.
    		draw.rectangle((0,0,width,height), outline=0, fill=0)
		# Retrieve system info
		cmd = "df -h | awk '$NF==\"/\"{printf \"HDD: %d/%dGB %s\", $3,$2,$5}'"
    		cmd = "df -h | awk '$NF==\"/\"{printf \"%s\", $5}'"
    		Disk = subprocess.check_output(cmd, shell = True )
    		# Draw icons
    		draw.text((x, top+25), unichr(61888), font=sys_icons_big, fill=255)
		# Draw text
		draw.text((x+52, top), "SD",  font=font_text_big, fill=255)
		draw.text((x+36, top+25), str(Disk), font=font_text_clock, fill=255)
		# Display
		disp.image(image)
		disp.display()
		# Publish the state to MQTT
		if first_run and mqtt_connection:
				mqttc.publish(STATE_TOPIC, modes[mode], DEFAULT_QOS, False)
		# Disable first_run
		first_run = False

	# Mode = CPU Temp
	elif mode == 6:
		# Draw a black filled box to clear the image.
    		draw.rectangle((0,0,width,height), outline=0, fill=0)
		# Retrieve system info
		cmd = "vcgencmd measure_temp | cut -d '=' -f 2 | head --bytes -1"
    		Temperature = subprocess.check_output(cmd, shell = True )
    		# Draw icons
    		draw.text((x, top), unichr(62152), font=sys_icons_big, fill=255)
		# Draw text
		draw.text((x+45, top), "CPU",  font=font_text_big, fill=255)
		draw.text((x+18, top+25), str(Temperature), font=font_text_clock, fill=255)
		# Display
		disp.image(image)
		disp.display()
		# Publish the state to MQTT
		if first_run and mqtt_connection:
				mqttc.publish(STATE_TOPIC, modes[mode], DEFAULT_QOS, False)
		# Disable first_run
		first_run = False

	# Mode = RAM
	elif mode == 7:
		# Draw a black filled box to clear the image.
    		draw.rectangle((0,0,width,height), outline=0, fill=0)
		# Retrieve system info
		cmd = "free -m | awk 'NR==2{printf \"%.2f%%\", $3*100/$2 }'"
   		MemUsage = subprocess.check_output(cmd, shell = True )
		# Draw icons

		# Draw text
		draw.text((x+40, top), "RAM",  font=font_text_big, fill=255)
    		draw.text((x, top+22),    str(MemUsage),  font=font_text_clock, fill=255)
		# Display
		disp.image(image)
		disp.display()
		# Publish the state to MQTT
		if first_run and mqtt_connection:
				mqttc.publish(STATE_TOPIC, modes[mode], DEFAULT_QOS, False)
		# Disable first_run
		first_run = False

	# Fallback to default mode, if mode is unknown
	else:
		mode = DEFAULT_MODE
	# Sleep as defined in refresh interval
	time.sleep(REFRESH_INTERVAL)
	
	
