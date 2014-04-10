#!/usr/bin/python

import json
import sys
import ownet
import mosquitto 
import time
import thread

class OwEventHandler(mosquitto.Mosquitto):

	def __init__(self,ip = "localhost", port = 1883, clientId = "1W2MQTT", user = "driver", password = "1234", prefix = "hardware/1-wire/",owserver = "127.0.0.1", owport = 4304):

		mosquitto.Mosquitto.__init__(self,clientId)

		self.prefix = prefix
		self.ip = ip
    		self.port = port
    		self.clientId = clientId
		self.user = user
    		self.password = password
    		
    		if user != None:
    			self.username_pw_set(user,password)

		self.will_set( topic = "system/1wire/", payload="Offline", qos=1, retain=True)
    		print "Connecting"
    		self.connect(ip,keepalive=10)
    		self.subscribe(self.prefix + "#", 0)
    		self.on_connect = self.mqtt_on_connect
    		self.on_message = self.mqtt_on_message
    		self.publish(topic = "system/1wire/", payload="Online", qos=1, retain=True)
    		
    		# 1 wire stuff
    		self.owserver = owserver
    		self.owport = owport
    		
    		
    		#Setup.

    		self.Updates = {}

		#thread.start_new_thread(self.ControlLoop,())	
		self.loop_start()

    		return
    		
    	def mqtt_on_connect(self, selfX,mosq, result):
    		print "MQTT connected!"
    		self.subscribe(self.prefix + "#", 0)
    
  	def mqtt_on_message(self, selfX,mosq, msg):
    		print("RECIEVED MQTT MESSAGE: "+msg.topic + " " + str(msg.payload))
    	
    		return
    	
    	def ControlLoop(self):
    		# schedule the client loop to handle messages, etc.
      		self.loop_forever()
		print "Closing connection to MQTT"
        	time.sleep(1)
        		
        def PollOwServer(self):
        	self.root = ownet.Sensor("/",self.owserver,self.owport)
        	self.sensorlist = self.root.sensorList()
        	
        	#If there is no sensors we probably failied. 
		if len(self.sensorlist) < 1:
			return False
			
		self.CheckSensors(self.sensorlist,True)
		
		self.alarm = ownet.Sensor("/alarm",self.owserver,self.owport)
		self.alarmlist = self.GetSensorsFromNameList(self.alarm.entryList())
		
		while(True):
			self.CheckSensors(self.alarmlist,False)
			self.alarmlist = self.GetSensorsFromNameList(self.alarm.entryList())
			
	def GetSensorsFromNameList(self,list):

		sensorlist = []

		for sensor in self.sensorlist:
			try:
				id = str(sensor.family) +"."+sensor.id	
			except:
				continue

			if id in list:
				sensorlist.append(sensor)

		#print sensorlist

		return sensorlist
	
	def Update(self,topic,value):

                #Filter already sent stuff. 
                if topic in self.Updates:
                        if value == self.Updates[topic]:
				#print "Rejected repeated message!"
                                return False

		self.Updates[topic] = value

		#Create json msg
                timestamp = time.time()
                msg = json.dumps({"time":timestamp,"value":value})

		#print "New event: " + topic
                self.publish(topic,msg,1)
                
                return True
                
        def UpdateDS2406(self,sensor, init = False):
        	
        	id = str(sensor.family) +"/"+ str(sensor.id)
        	values = sensor.sensed_ALL.split(",")
		trigger = sensor.latch_ALL.split(",")
        	
        	#Loop trough pins
        	for i in range(0,len(values)):
        		topic = self.prefix+id+"/"+str(i)
        		value = values[i]
        	
        		self.Update(topic,value)
        		
        	sensor.latch_BYTE = 0
        	
        	if init:
        		if not sensor.set_alarm == 311:
				sensor.set_alarm = 311		
        		
        	return
		
	def CheckSensors(self,sensorlist,init=False):
		for sensor in sensorlist:
			if not hasattr(sensor,"type"):
				continue
			
			stype = sensor.type
			if stype == "DS2406":
				self.UpdateDS2406(sensor,init)
			else:
				continue
	
		return		
			
		
if __name__ == '__main__':
	
	EventHandler = OwEventHandler()
	EventHandler.PollOwServer()
	
	
