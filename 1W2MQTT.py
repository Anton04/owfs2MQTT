#!/usr/bin/python

import json
import sys
import ownet
import mosquitto 
import time
import thread
import operator
from terminaltables import AsciiTable
import os

class OwEventHandler(mosquitto.Mosquitto):

	def __init__(self,ip = "localhost", port = 1883, clientId = "1W2MQTT", user = "driver", password = "1234", prefix = "1-wire",owserver = "127.0.0.1", owport = 4304):

		mosquitto.Mosquitto.__init__(self,clientId)

		self.prefix = prefix
		self.ip = ip
    		self.port = port
    		self.clientId = clientId
		self.user = user
    		self.password = password
    		
    		if user != None:
    			self.username_pw_set(user,password)

		self.will_set( topic = "system/" + self.prefix, payload="Offline", qos=1, retain=True)
    		print "Connecting"
    		self.connect(ip,keepalive=10)
    		self.subscribe(self.prefix + "/#", 0)
    		self.on_connect = self.mqtt_on_connect
    		self.on_message = self.mqtt_on_message
    		self.publish(topic = "system/"+ self.prefix, payload="Online", qos=1, retain=True)
    		
    		# 1 wire stuff
    		self.owserver = owserver
    		self.owport = owport
		    		
    		
    		#Setup.

    		self.Updates = {}
		self.LastChecked = {}
		self.alarmlist = []		
		self.LastCycled = None
		self.cycletime = 0		
		self.LastUpdate = ""		
		self.MQTTstatus = ""
		

		#thread.start_new_thread(self.ControlLoop,())	
		self.loop_start()

    		return
    		
    	def mqtt_on_connect(self, selfX,mosq, result):
    		self.MQTTstatus = "MQTT connected!"
    		self.subscribe(self.prefix + "/#", 0)
    
  	def mqtt_on_message(self, selfX,mosq, msg):
    		self.MQTTstatus = "RECIEVED MQTT MESSAGE: "+msg.topic + " " + str(msg.payload)
    	
    		return
    	
    	def ControlLoop(self):
    		# schedule the client loop to handle messages, etc.
      		self.loop_forever()
		self.MQTTstatus =  "Closing connection to MQTT"
        	time.sleep(1)
        		
        def PollOwServer(self):
		
        	#Init connection.
		self.root = ownet.Sensor("/",self.owserver,self.owport)

		#Create a list which keeps track of when sensors was read. 
		self.LastChecked = self.CheckForNewSensors()
		
		#Init alarm path
		self.alarm = ownet.Sensor("/alarm",self.owserver,self.owport)

		#Check all sensors. 
		self.CheckSensors(self.LastChecked.keys())

		now = time.time()		

		while(True):

			try:
			
				#Update the LastChecked list with added or removed sensors.  
        	                self.LastChecked = self.CheckForNewSensors(self.LastChecked)

				#Do some iterations then check for new sensors.			
				for f in range(0,30):

					#Sleep some to not overload the system with requests. 
		                 	time.sleep(0.1)
	
					#Time the loop
					lasttime = now
					now = time.time()
					self.cycletime = now-lasttime

					#Check if there is alarms and check them.
					self.alarmlist = self.GetAlarmList()
					for sensor in self.alarmlist:
						sensor.alarm = now
		
					self.CheckSensors(self.alarmlist,False)
				
					#Update old values and non alarm sensors. Check one each iteration.
	
					#Update the LastChecked list with added or removed sensors.  
	        		        self.LastChecked = self.CheckForNewSensors(self.LastChecked)

					#Try to find the oldest one. 
					try:
						(sensor,checked) = self.GetOldestUpdate()[0]
					except IndexError:
						continue
			
					#Avoid updating sensors more than once each second.
					if (now - checked) < 1.0:
						continue
			
					#Check the sensor. 
					self.CheckSensors([sensor])
					self.LastCycled = sensor

					#Debug print.
					if f%1==0:
                        			self.PrintLastCheckedTimes()

			except OverflowError:
				print "OverflowError!!"
				

		return 

	#Check for new sensors and remove old ones. 
	def CheckForNewSensors(self,old_dict={}):
                sensorlist = self.root.sensorList()
		new_dict = {}
		now = time.time()

		for sensor in sensorlist:
			sensor.present = True
			sensor.alarm = 0
			sensor.initiated = False

		#Make a new list
		for sensor in sensorlist:
			try:
				#Copy update time from old list if possible. 
				new_dict[sensor] = old_dict[sensor]
				
			except KeyError:
				#Not in old so new snesor. Indicate that it has never been checked. 
				sensor.present = True
				new_dict[sensor] = 0.0
				sensor.initiated = False
			
		#Readd sensors that disconnected but pospone reading. 
		for sensor in old_dict:
			if not sensor in new_dict:
				sensor.present = False
				new_dict[sensor]=old_dict[sensor]

		return new_dict

	#Returns a list with the N sensors with oldest update times. 
	def GetOldestUpdate(self,n=1):		
		return sorted(self.LastChecked.items(), key=operator.itemgetter(1))[:n]

	def PrintLastCheckedTimes(self):
		dictlist = [["Sensor","Time since update","update bar","Update reason","Present","Initiated"]]
		now = time.time()

		for sensor, value in self.LastChecked.iteritems():
			try:
                                id = str(sensor.family) +"."+sensor.id
                        except:
				continue
			deltatime = int(now-value)
			bar = deltatime
			if bar > 20:
				bar = 20

			update = "  "
			try:
				if sensor == self.LastCycled:
					update = " <-"
			except:
				pass

			if sensor in self.alarmlist:
				update = "(!)"
			
			try:
				if now - sensor.alarm < 3.0:
					update = "(!)"
		
			except:
				update += "_"

			try:
				if sensor.present:
					present="Y"
				else:
					present="N"
			except:
				present="-"
				
			try:
				initiated = sensor.initiated
			except:
				initiated = " "

    			temp = [id,str(deltatime),("*" * bar) + (" " * (20-bar)),update,present,initiated ]
    			dictlist.append(temp)

		table = AsciiTable(dictlist)
		
		#Print topics
		dictlist2=[["  ","Topic","Payload"]]

		for topic, payload in self.Updates.iteritems():
			updated = " "

			if topic == self.LastUpdate:
				self.LastUpdate = ""
				updated = "*"
	
			temp = [updated ,topic,str(payload)]		

			dictlist2.append(temp)


		table2 = AsciiTable(dictlist2)		
			
		os.system('clear')
		print "-" * 50
		print " " * 15 + "1WIRE TO MQTT"
		print "-" * 50
		print " "		
		print "Owserver traffic"	
		print table.table
		print " "
                print "Cycle time = %f" % self.cycletime

		print " "
		print "MQTT traffic"
		print table2.table
		print " "
		print self.MQTTstatus

		print "\n"*4
		print "Created by Anton Gustafsson"

		return 		        

	#This function takes the format deliverd from alarm and turns it into an sensor object list. 			
	def GetAlarmList(self):

		list = self.alarm.entryList()
		sensorlist = []
		all_sensors = self.LastChecked.keys()
		now = time.time()

		#Loop trough all known sensors and see if they are in the list provided. 
		for sensor in all_sensors:
			try:
				id = str(sensor.family) +"."+sensor.id	
			except:
				continue

			if id in list:
				sensor.alarm = now
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
		self.LastUpdate = topic

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
        		topic = self.prefix+"/"+id+"/"+str(i)

			try:
        			value = int(values[i])
			except:
				value = values[i]
        	
        		self.Update(topic,value)
        		
        	sensor.latch_BYTE = 0
        	
        	if init:
        		if not sensor.set_alarm == 311:
				sensor.set_alarm = 311		
        		
        	return
		
	def CheckSensors(self,sensorlist,init=False):
		for sensor in sensorlist:
			now = time.time()
			self.LastChecked[sensor]=now
			sensor.LastChecked = now
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
	
	
