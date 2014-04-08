#!/usr/bin/python


import sys

import mosquitto 

class OwEventHandler(mosquitto.Mosquitto):

	def __init__(self,ip = "localhost", port = 1883, clientId = "owfs2MQTT", user = None, password = None, prefix = "hardware/1-wire/"):
		mosquitto.Mosquitto.__init__(self,clientId)

		self.prefix = prefix
		self.ip = ip
    		self.port = port
    		self.clientId = clientId
		self.user = user
    		self.password = password
    		
    		if user != None:
    			self.username_pw_set(user,password)

    		print "Connecting"
    		self.connect(ip)
    		self.subscribe(self.prefix + "#", 0)
    		self.on_connect = self.mqtt_on_connect
    		self.on_message = self.mqtt_on_message
    		
    		return
    		
    	def mqtt_on_connect(self, selfX,mosq, result):
    		print "MQTT connected!"
    		self.subscribe(self.prefic + "#", 0)
    
  	def mqtt_on_message(self, selfX,mosq, msg):
    		print("RECIEVED MQTT MESSAGE: "+msg.topic + " " + str(msg.payload))
    	
    		return
